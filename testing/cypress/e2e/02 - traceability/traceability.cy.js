describe("Traceabilit page", () => {
  beforeEach(function () {
    cy.fixture("global_data").then((data) => {
      // "this" is still the test context object
      this.data = data;
      cy.request("DELETE", data.resetprodURL);
      cy.visit(data.progressURL);
    });
  });

  it("perform login and logout", function () {
    cy.get("#username").should("exist").type(this.data.username);
    cy.get("#password").should("exist").type(this.data.password);
    cy.get(".q-btn__content").click();
    cy.get(".app-bar-user-name", { timeout: 30000 }).should("be.visible");

    //CREATING A WORKING ORDER
    cy.get(".q-btn__content > .q-icon").click();
    cy.get('[href="/app/production"] > .q-tab__content').click();
    cy.url().should("include", "/production/overview/workorder");
    cy.get(".q-pl-xs > .col-auto > .q-btn", { timeout: 30000 })
      .should("be.visible")
      .click();
    cy.get(
      ".q-py-sm > :nth-child(1) > .q-field > .q-field__inner > .q-field__control"
    ).type("00001");
    cy.get(".col-1 > .q-field > .q-field__inner > .q-field__control").type(
      "10"
    );
    cy.get(
      ".col-3 > .q-field > .q-field__inner > .q-field__control > .q-field__append > .q-icon"
    ).click();
    cy.get("#00TEST").click();
    cy.get(".q-mt-md > :nth-child(1) > .q-btn > .q-btn__content").click();

    //SELECTING THE WORKING ORDER
    cy.get(".q-toolbar > .q-btn > .q-btn__content > .q-icon").click();
    cy.get('[href="/app/operator/select-job"] > .q-tab__content').click();
    cy.url().should("include", "operator/select-job/confirm");
    cy.get(".bg-theme-blue > .q-btn__content", { timeout: 30000 })
      .should("be.visible")
      .click();

    cy.get(":nth-child(1) > .q-btn > .q-btn__content > .row").click();

    cy.get(
      ":nth-child(1) > .q-mb-lg > .q-field > .q-field__inner > .q-field__control > .q-field__control-container"
    ).type("1111");
    cy.get(
      ":nth-child(2) > .q-mb-lg > .q-field > .q-field__inner > .q-field__control > .q-field__control-container"
    ).type("2222");
    cy.get(
      ":nth-child(3) > .q-mb-lg > .q-field > .q-field__inner > .q-field__control > .q-field__control-container"
    ).type("3333");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row").click();
    cy.get(".q-checkbox__inner");
    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row").click();

    //SELECTING THE second step
    cy.url().should("include", "operator/select-job/confirm");
    cy.get(".bg-theme-blue > .q-btn__content", { timeout: 30000 })
      .should("be.visible")
      .click();

    cy.get(":nth-child(1) > .q-btn > .q-btn__content > .row").click();

    cy.get(".q-mb-md > .text-h2").should("be.visible");

    cy.get(":nth-child(1) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(2) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(3) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(4) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(5) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(6) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(7) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(8) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(9) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(10) > .q-toggle > .q-toggle__inner").click();

    cy.get(".bg-primary > .q-btn__content > .block").click();

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    cy.get(".text-h3").should("include.text", "CREAZIONE STACK-UP");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    cy.get(".text-h3").should("include.text", "Numero Pressatura");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    cy.get(".text-h3").should("include.text", "Verifiche POST-Pressatura");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    cy.get(".text-h3").should("include.text", "AVVIO PRESSATURA");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    cy.get(".text-h3").should("include.text", "Ciclo di Pressatura Utilizzato");

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    //SELECTING THE third step
    cy.url().should("include", "operator/select-job/confirm");
    cy.get(".bg-theme-blue > .q-btn__content", { timeout: 30000 })
      .should("be.visible")
      .click();

    cy.get(":nth-child(1) > .q-btn > .q-btn__content > .row").click();

    cy.get(".q-mb-md > .text-h2")
      .should("be.visible")
      .should("include.text", "Select batch serial");

    cy.get(":nth-child(1) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(2) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(3) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(4) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(5) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(6) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(7) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(8) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(9) > .q-toggle > .q-toggle__inner").click();
    cy.get(":nth-child(10) > .q-toggle > .q-toggle__inner").click();

    cy.get(".bg-primary > .q-btn__content > .block").click();

    cy.get(":nth-child(2) > .q-btn > .q-btn__content > .row")
      .should("be.visible")
      .click();

    //JOB DONE
    cy.url().should("include", "operator/select-job/confirm");
    cy.get(".text-body1")
      .should("be.visible")
      .should("include.text", "Good evening.");

    //SELECTING THE WORKING ORDER
    cy.get(".q-toolbar > .q-btn > .q-btn__content > .q-icon").click();
    cy.get('[href="/app/traceability"] > .q-tab__content').click();
    cy.url().should("include", "traceability/serials");
  });
});
