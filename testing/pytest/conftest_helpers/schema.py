from datetime import datetime
from pydantic import BaseModel, Field
from arango import ArangoClient


class DBIndex(BaseModel):
    type: str | None = 'persistent'
    fields: list[str]
    name: str
    storedValues: list[str] | None = Field(None, exclude=True)
    unique: bool | None = None


class Collection(BaseModel):
    name: str
    indexes: list[DBIndex] | None = []
    default_records: list[dict] | None = []


COLLECTIONS = [
    Collection(name='Batch', indexes=[
        DBIndex(fields=['job_key, canceled'], name='batch-job-canceled'),
        DBIndex(fields=['work_order_key, phase_key, canceled'], name='batch-wo-phase-canceled')
    ]),
    Collection(name='batch_serial'),
    Collection(name='can_use_print_template'),
    Collection(name='Config', default_records=[
        dict(
            _key='company_logo',
            value=None
        ),
        dict(
            _key='company_name',
            value='PROGRESS PLATFORM'
        ),
        dict(
            _key='default_operation_parameters',
            parallel_job_allowed=True,
            display_job_timer=False,
            step_check=False,
            step_check_force_order=False,
            production_batch_qt=1,
            max_offline=300,
            std_processing_time=60
        ),
        dict(
            _key='show_unassigned_jobs_to_operators',
            value=True
        ),
        dict(
            _key='allow_independent_reordering_of_job_queues',
            value=False
        ),
        dict(
            _key='allow_serial_delete',
            value=True
        ),
        dict(
            _key='enable_inventory_management',
            value=False
        ),
        dict(
            _key='default_production_position',
            value='IN'
        ),
        dict(
            _key='default_consumption_position',
            value='IN'
        ),
        dict(
            _key='operator_cost',
            value=25
        ),
        dict(
            _key='system_counters',
            work_orders='default',
            warehouse_missions='default',
            counting_sessions='default',
            positions='default',
            tasks='default'
        )
    ]),
    Collection(name='contains'),
    Collection(name='Counter', default_records=[
        dict(
            _key='default',
            next_tick=1,
            template=['%y', '#6'],
            frequency="year",
            reset_date=datetime.today().replace(
                year=datetime.today().year + 1, month=1, day=1,
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
        )
    ]),
    Collection(name='CustomField', default_records=[
        dict(
            _key='separator',
            name='Separator',
            type='separator',
            default_label=None,
            default_hint=None
        )
    ]),
    Collection(name='CustomData'),
    Collection(name='CustomListValue', indexes=[
        DBIndex(fields=['field_key'], name='clv-field')
    ]),
    Collection(name='Department'),
    Collection(name='Event', indexes=[
        DBIndex(fields=['issue_key'], name='event-issue'),
        DBIndex(fields=['serial_key'], name='event-serial'),
        DBIndex(fields=['timestamp'], name='event-timestamp')
    ]),
    Collection(name='has_tag'),
    Collection(name='movement', indexes=[
        DBIndex(fields=['product_key', 'status', 'stage'], name='movement-product'),
        DBIndex(fields=['serial_key'], name="movement-serial"),
        DBIndex(fields=['list_key'], name="movement-list"),
        DBIndex(fields=['start', 'end'], name="movement-time-range"),
    ]),
    Collection(name='InventoryCountSession'),
    Collection(name='InventoryCountAssignment'),
    Collection(name='InventorySnapshot'),
    Collection(name='InventorySnapshotItem'),
    Collection(name='inventory_count_position_complete'),
    Collection(name='inventory_count_record'),
    Collection(name='Issue', indexes=[
        DBIndex(fields=['issue_type_key'], name="issue-type"),
        DBIndex(fields=['created'], name='issue-created-time'),
        DBIndex(fields=['open'], name='issue-open'),
        DBIndex(fields=['critical'], name='issue-critical')
    ]),
    Collection(name='issue_rel'),
    Collection(name='IssueType'),
    Collection(name='Job', indexes=[
        DBIndex(fields=['wo_key, phase_key, assigned_to, stage'], name='job-target'),
        DBIndex(fields=['assigned_to, stage'], name='job-assignment'),
        DBIndex(fields=['active'], name='job-active')
    ]),
    Collection(name='is_in_position',
        indexes=[
            DBIndex(fields=['serial_key'], name='inventory-serial')
        ],
        default_records=[
            dict(
                _key='IN',
                code='IN',
                owned=True,
                available=True,
                disposable=False,
                extra=None
            ),
            dict(
                _key='OUT',
                code='OUT',
                owned=False,
                available=False,
                disposable=False,
                extra=None
            )
        ]
    ),
    Collection(name='Media'),
    Collection(name='media_connection'),
    Collection(name='message'),
    Collection(name='Operation'),
    Collection(name='Phase', indexes=[
        DBIndex(fields=['product_key, operation_key'], name='phase-product-operation')
    ]),
    Collection(name='Position', indexes=[
        DBIndex(fields=['_key'], storedValues=['code'], name='position-key'),
        DBIndex(fields=['code'], storedValues=['_key'], name='position-code'),
        DBIndex(fields=['_key', 'code'], name='position-key-code')
    ]),
    Collection(name='PrintTemplate'),
    Collection(name='Product', indexes=[
        DBIndex(fields=['_key'], storedValues=['code'], name='product-key-code'),
        DBIndex(fields=['code'], storedValues=['_key'], name='product-code-key')
    ]),
    Collection(
        name='Queue',
        indexes=[
            DBIndex(fields=['type, independent, subqueue_target_key'], name='queue-type-independent-target'),
            DBIndex(fields=['subqueue_target_key'], name="queue-target")
        ],
        default_records=[
            dict(
                type='s',
                site_key='0',
                work_orders=[]
            )
        ]
    ),
    Collection(name='requires'),
    Collection(name='Serial', indexes=[
        DBIndex(fields=['_key'], storedValues=['code'], name='serial-key-code'),
        DBIndex(fields=['code'], storedValues=['_key'], name='serial-code-key'),
        DBIndex(fields=['wo_key', 'released'], name='serial-wo'),
        DBIndex(fields=['product_key', 'released'], name='serial-product'),
        DBIndex(fields=['released'], name='serial-released'),
    ]),
    Collection(name='Site'),
    Collection(name='Step'),
    Collection(name='StepExecutionData', indexes=[
        DBIndex(fields=['batch_key, step_key, status, canceled'], name='sxd-batch-step-status-canceled')
    ]),
    Collection(name='Tag'),
    Collection(name='Task', indexes=[
        DBIndex(fields=['task_type_key'], name='task-type'),
        DBIndex(fields=['status'], name='task-status'),
        DBIndex(fields=['code'], name='task-code', unique=True),
        DBIndex(fields=['assigned_to', 'status'], name='task-assignee-status'),
    ]),
    Collection(name='TaskType'),
    Collection(name='task_rel'),
    Collection(name='Token'),
    Collection(name='User', default_records=[
        dict(
            username='cadmin',
            name='Utente',
            surname='Amministratore',
            active=True,
            psw_hash='$2b$12$LJ3m4ys3HIssFIGMqx0E3OIq2GRNyGeUxBRjLJSAVaKSrv2VMQHIS',
            scope='admin production library operator quality warehouse task traceability reporting',
            site_key='0',
            reset_password=True
        ),
    ]),
    Collection(name='UserSession'),
    Collection(name='wip', indexes=[
        DBIndex(fields=['wo_key'], name='wip-wo'),
        DBIndex(fields=['serial_key'], name='wip-serial'),
        DBIndex(fields=['_to, wo_key, active, serial_key'], name='wip-target'),
    ]),
    Collection(name='MovementList', indexes=[
        DBIndex(fields=['code'], storedValues=['_key'], name="list-code-key"),
        DBIndex(fields=['_key'], storedValues=['code'], name="list-key-code"),
        DBIndex(fields=['status', 'assigned_to'], name="list-status-assignee")
    ]),
    Collection(name='WorkOrder', indexes=[
        DBIndex(fields=['_key'], storedValues=['code'], name='workorder-key-code'),
        DBIndex(fields=['code'], storedValues=['_key'], name='workorder-code-key')
    ]),
    Collection(name='WorkSession', indexes=[
        DBIndex(fields=['work_order_key'], name='ws-wo'),
        DBIndex(fields=['job_key, canceled'], name='ws-job-canceled'),
        DBIndex(fields=['user_key, active'], name='ws-user-active'),
        DBIndex(fields=['batch_key, canceled'], name='ws-batch-canceled'),
    ]),
    Collection(name='event_source'),  # Edge collection for parent-child event relationships
]


def initialize_schema(sys_db) -> object:
    """
    Initialize the PROGRESS_TEST database with all collections, indexes, and default records.

    Args:
        sys_db: ArangoDB system database handle

    Returns:
        Database handle for PROGRESS_TEST
    """
    try:
        sys_db.create_database(
            "PROGRESS_TEST",
            users=[{"username": "root", "password": "", "active": True}]
        )
    except Exception as e:
        if "database already exists" not in str(e).lower():
            raise

    # Get the ArangoDB host URL from the sys_db connection
    # BasicConnection stores hosts in _hosts list (python-arango 8.x)
    host_url = sys_db._conn._hosts[0]
    db = ArangoClient(hosts=host_url).db("PROGRESS_TEST", username="root", password="")

    for c in COLLECTIONS:
        # If collection name starts with lowercase it's an edge collection
        is_edge = c.name[0].islower()
        try:
            db.create_collection(name=c.name, edge=is_edge)
        except Exception as e:
            if "duplicate name" not in str(e).lower() and "collection already exists" not in str(e).lower():
                raise

        collection = db.collection(c.name)

        for index in c.indexes:
            try:
                collection.add_index(index.model_dump(exclude_none=True))
            except Exception:
                pass  # Index may already exist

        if c.default_records:
            try:
                collection.insert_many(c.default_records)
            except Exception:
                pass  # Records may already exist

    return db
