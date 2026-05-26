import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

console = Console()

# Configuration
REGISTRY = "registry.gitlab.com/progresslab/progress-platform"
IMAGES = ["api", "app", "wf-sys-worker", "warehouse"]
STACK_NAME = "progress"
SERVICES = [f"{STACK_NAME}_{image}" for image in IMAGES]
RELEASE_LOG_PATH = Path("/opt/progress/release")


def run_docker_command(cmd: List[str], capture_output: bool = True) -> Tuple[bool, str]:
    """Run a docker command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False,
            timeout=600  # 10 minute timeout
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else result.stdout
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 10 minutes"
    except Exception as e:
        return False, str(e)


def pull_image(image_name: str, tag: str, progress: Progress, task_id: TaskID) -> Tuple[str, bool, str]:
    """Pull a Docker image with progress tracking."""
    full_image_name = f"{REGISTRY}/{image_name}:{tag}"
    cmd = ["docker", "pull", full_image_name]

    # Start the pull process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Update progress while pulling
    last_status = f"Pulling {image_name}..."
    error_output = []

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            line = output.strip()
            # Extract meaningful status from docker output
            if "Pulling" in line or "Downloading" in line or "Extracting" in line or "Pull complete" in line:
                # Clean up the line for display (remove ANSI codes if any)
                clean_line = line.replace('\r', '').replace('\x1b[', '').split('\x1b')[0]
                last_status = f"Pulling {image_name}... {clean_line[:60]}"
                progress.update(task_id, description=last_status)
            elif "error" in line.lower() or "failed" in line.lower():
                error_output.append(line)

    # Wait for process to complete
    process.wait()
    success = process.returncode == 0
    error_text = "\n".join(error_output) if error_output else ""

    return image_name, success, error_text


def update_service(service_name: str, image_name: str, tag: str, progress: Progress, task_id: TaskID) -> Tuple[str, bool, str]:
    """Update a Docker service with progress tracking."""
    full_image_name = f"{REGISTRY}/{image_name}:{tag}"
    cmd = ["docker", "service", "update", "--image", full_image_name, "--force", service_name]

    success, output = run_docker_command(cmd, capture_output=True)

    return service_name, success, output if not success else ""


def write_release_log(tag: str) -> None:
    """Write release log entry."""
    try:
        RELEASE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        with open(RELEASE_LOG_PATH, "a") as f:
            f.write(f"{timestamp} {tag}\n")
        console.print(f"[green]✓[/green] Release log entry added: {timestamp} {tag}")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow]  Warning: Could not write release log: {e}")


def show_service_status() -> None:
    """Show current Docker service status."""
    try:
        result = subprocess.run(
            ["docker", "service", "ls"],
            capture_output=True,
            text=True,
            check=True
        )
        console.print("\n[bold]Current Services:[/bold]")
        console.print(result.stdout)
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow]  Could not retrieve service status: {e}")


def update(
    tag: Optional[str] = typer.Argument(None, help="Image tag to deploy"),
    services: Optional[List[str]] = typer.Option(None, "--service", "-s", help="Specific services to update (default: all)"),
    skip_pull: bool = typer.Option(False, "--skip-pull", help="Skip pulling images (use existing local images)"),
) -> None:
    """
    Update Docker services with new image tags.

    This command pulls Docker images and updates the corresponding services in parallel.
    """
    # Get tag from argument or prompt
    if not tag:
        tag = typer.prompt("Please enter the image tag to deploy")
        if not tag:
            console.print("[red]❌ Error: No tag provided. Aborting.[/red]")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Using tag: [bold]{tag}[/bold]\n")

    # Determine which services/images to update
    if services:
        # Filter to only requested services
        service_indices = []
        for i, service in enumerate(SERVICES):
            if any(s in service.lower() for s in [s.lower() for s in services]):
                service_indices.append(i)

        if not service_indices:
            console.print("[red]❌ Error: No matching services found.[/red]")
            raise typer.Exit(1)

        images_to_pull = [IMAGES[i] for i in service_indices]
        services_to_update = [(SERVICES[i], IMAGES[i]) for i in service_indices]
    else:
        images_to_pull = IMAGES
        services_to_update = list(zip(SERVICES, IMAGES))

    console.print(f"[bold]🚀 Starting image pull and service update process for tag '{tag}'...[/bold]\n")

    # Pull images in parallel
    if not skip_pull:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            tasks = {}
            with ThreadPoolExecutor(max_workers=len(images_to_pull)) as executor:
                # Start all pull tasks
                futures = {}
                for image in images_to_pull:
                    task_id = progress.add_task(f"Pulling {image}...", total=None)
                    tasks[image] = task_id
                    future = executor.submit(pull_image, image, tag, progress, task_id)
                    futures[future] = (image, task_id)

                # Wait for all pulls to complete
                pull_results = []
                for future in as_completed(futures):
                    image, task_id = futures[future]
                    try:
                        image_name, success, error = future.result()
                        progress.update(task_id, completed=True)
                        if success:
                            progress.update(task_id, description=f"[green]✓[/green] Pulled {image_name}")
                        else:
                            progress.update(task_id, description=f"[red]✗[/red] Failed to pull {image_name}")
                        pull_results.append((image_name, success, error))
                    except Exception as e:
                        progress.update(task_id, description=f"[red]✗[/red] Error pulling {image}: {str(e)}")
                        pull_results.append((image, False, str(e)))

            # Check for failures
            failed_pulls = [r for r in pull_results if not r[1]]
            if failed_pulls:
                console.print("\n[red]❌ Error: One or more image pulls failed:[/red]")
                for image, _, error in failed_pulls:
                    console.print(f"  [red]✗[/red] {image}")
                    if error:
                        console.print(f"    {error[:200]}")
                raise typer.Exit(1)

        console.print("\n[green]✅ All images pulled successfully.[/green]\n")

    # Update services in parallel
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        tasks = {}
        with ThreadPoolExecutor(max_workers=len(services_to_update)) as executor:
            # Start all update tasks
            futures = {}
            for service_name, image_name in services_to_update:
                task_id = progress.add_task(f"Updating {service_name}...", total=None)
                tasks[service_name] = task_id
                future = executor.submit(update_service, service_name, image_name, tag, progress, task_id)
                futures[future] = (service_name, task_id)

            # Wait for all updates to complete
            update_results = []
            for future in as_completed(futures):
                service_name, task_id = futures[future]
                try:
                    svc_name, success, error = future.result()
                    progress.update(task_id, completed=True)
                    if success:
                        progress.update(task_id, description=f"[green]✓[/green] Updated {svc_name}")
                    else:
                        progress.update(task_id, description=f"[red]✗[/red] Failed to update {svc_name}")
                    update_results.append((svc_name, success, error))
                except Exception as e:
                    progress.update(task_id, description=f"[red]✗[/red] Error updating {service_name}: {str(e)}")
                    update_results.append((service_name, False, str(e)))

        # Check for failures
        failed_updates = [r for r in update_results if not r[1]]
        if failed_updates:
            console.print("\n[red]❌ Error: One or more service updates failed:[/red]")
            for service, _, error in failed_updates:
                console.print(f"  [red]✗[/red] {service}")
                if error:
                    console.print(f"    {error[:200]}")
            raise typer.Exit(1)

    console.print(f"\n[green]🎉 All services updated successfully to tag '{tag}'![/green]\n")

    # Write release log
    console.print("[bold]📋 Adding release log entry[/bold]")
    write_release_log(tag)

    # Show service status
    show_service_status()
