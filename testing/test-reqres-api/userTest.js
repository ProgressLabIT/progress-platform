const request = require("supertest");
const expect = require("chai").expect;
const { faker } = require("@faker-js/faker");
const reqres = require("../config/progress.config.json");
const data = require("../test-data/progress-data.json");

const randomName = faker.person.fullName();
const randomJob = faker.person.jobTitle();

let token = "";

describe("Authenticate user and get options", () => {
  it("should successfully authenticate with auth post", (done) => {
    request(reqres.baseUrl)
      .post("/api/auth")
      .send(data.user)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.status).to.be.equal(200);
        expect(res.body.detail.action).to.be.equal("start_session");
        expect(res.body.detail.token).not.to.be.null;
        token = res.body.detail.token;
        done();
      });
  });
});
