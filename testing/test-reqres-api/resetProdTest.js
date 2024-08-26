const request = require("supertest");
const expect = require("chai").expect;
const api = require("../config/progress.config.json");

describe("Reset PROD API tests", () => {
  it("should successfully reset the prod envinronment", (done) => {
    request(api.baseUrl)
      .delete("/api/reset/prod")
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body).to.be.equal(
          "Reset of Production and Traceability data successful"
        );
        done();
      });
  });
});
