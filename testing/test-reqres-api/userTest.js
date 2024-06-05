const request = require("supertest");
const expect = require("chai").expect;
const { faker } = require("@faker-js/faker");
const api = require("../config/progress.config.json");
const data = require("../test-data/progress-data.json");

const randomName = faker.person.fullName();
const randomJob = faker.person.jobTitle();

let token = "";
let session_key = "";
let session_user_key = "";

describe("Authenticate user and get options", () => {
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
        expect(res.body.detail.token).not.to.be.null;
        token = res.body.detail.token;
        done();
      });
  });

  it("should be able to start a session", (done) => {
    request(api.baseUrl)
      .post("/api/session")
      .send({
        user_key: data.user_key,
      })
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .set("Authorization", `Bearer ${token}`)
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.status).to.be.equal(200);
        expect(res.body.detail.scope).not.to.be.null;
        expect(res.body.detail.preferences).not.to.be.null;
        user_key = res.body.detail.user_key;
        session_key = res.body.detail.session_key;
        done();
      });
  });

  it("should be able to retrieve job assignment", (done) => {
    request(api.baseUrl)
      .get("/api/job-assignment")
      .query({ user_key: session_user_key })
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .set("authorization", `Bearer ${token}`)
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.status).to.be.equal(200);
        expect(res.body.detail).not.to.be.null;
        done();
      });
  });

  it("should be able to close the session", (done) => {
    request(api.baseUrl)
      .delete(`/api/session/${session_key}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .set("authorization", `Bearer ${token}`)
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.detail).to.be.equal("Session closed successfully");
        done();
      });
  });

  it("should not be able to start a session again", (done) => {
    request(api.baseUrl)
      .post("/api/session")
      .send({
        user_key: data.user_key,
      })
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .set("authorization", `Bearer ${token}`)
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(401);
        expect(res.body.detail.message).to.be.equal(
          "Could not validate credentials."
        );
        done();
      });
  });

  it("it should not be able to authenticate with wrong credential", (done) => {
    request(api.baseUrl)
      .post("/api/auth")
      .send(data.user_wrong)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(401);
        expect(res.body.detail.message).to.be.equal(
          "Could not validate credentials."
        );
        done();
      });
  });
});
