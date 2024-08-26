describe("Login page", () => {
  beforeEach(function () {
    cy.fixture("global_data").then((data) => {
      // "this" is still the test context object
      this.data = data;
      cy.visit(data.progressURL);
    });
  });

  it("perform login and logout", function () {
    cy.get("#username").should("exist").type(this.data.username);
    cy.get("#password").should("exist").type(this.data.password);
    cy.get(".q-btn__content").click();
    cy.get(".app-bar-user-name", { timeout: 30000 }).click();
    cy.get(".q-item__label").click();
    cy.get("#username", { timeout: 30000 }).should("exist");
    cy.get("#password", { timeout: 30000 }).should("exist");
  });
});
