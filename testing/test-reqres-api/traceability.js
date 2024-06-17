const request = require("supertest");
const expect = require("chai").expect;
const api = require("../config/progress.config.json");
const data = require("../test-data/progress-data.json");

let cookieObj = "";

describe("Traceability tests", () => {
  before(() => {});

  it("should successfully authenticate with auth post", (done) => {
    request(api.baseUrl)
      .post("/api/auth")
      .send(data.user)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.status).to.be.equal(200);
        expect(res.body.detail.action).to.be.equal("start_session");
        expect(res.header["set-cookie"]).not.to.be.null;
        cookieObj = res.header["set-cookie"];
        done();
      });
  });
});
