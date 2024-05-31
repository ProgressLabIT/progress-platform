describe("template spec", () => {
  beforeEach(() => {
    cy.visit("http://localhost:9000/login");
  });

  it("perform login and logout", () => {
    cy.get("#username").should("exist").type("simone");
    cy.get("#password").should("exist").type("simone");
    cy.get(".q-btn__content").click();
    cy.get(".app-bar-user-name", { timeout: 30000 }).click();
    cy.get(".q-item__label").click();
    cy.get("#username", { timeout: 30000 }).should("exist");
    cy.get("#password", { timeout: 30000 }).should("exist");
  });
});
