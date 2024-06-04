const request = require("supertest");
const expect = require("chai").expect;
const reqres = require("../config/progress.config.json");

describe("GET Hello", () => {
  it("should successfully pass the test for get Hello api without query param", (done) => {
    request(reqres.baseUrl)
      .get("/api/hello")
      // .set('Accept', 'application/json')
      // .set('Content-Type', 'application/json')
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body).to.be.equal("Hi!");
        done();
      });
  });
});
