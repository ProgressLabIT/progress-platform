const request = require("supertest");
const expect = require("chai").expect;
const api = require("../config/progress.config.json");
const data = require("../test-data/progress-data.json");

describe("Test Kafka topic ", () => {
  it("don't really care about the first delete, it is just to clean it up", (done) => {
    request(api.baseUrl)
      .delete(`/api/kafka/topic/${data["kafka_topic"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        done();
      });
  });

  it("should successfully create the kafka topic", (done) => {
    request(api.baseUrl)
      .put(`/api/kafka/topic/${data["kafka_topic"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.be.equal(
          `Topic ${data["kafka_topic"]} created`
        );
        done();
      });
  });

  it("should be able to retrieve info on the just created topics", (done) => {
    request(api.baseUrl)
      .get(`/api/kafka/topic/${data["kafka_topic"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.contain("Topic name");
        done();
      });
  });

  it("should fail on not present topic", (done) => {
    request(api.baseUrl)
      .get(`/api/kafka/topic/${data["kakafka_topic_not_present"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.contain("Unknown topic or partition");
        done();
      });
  });

  it("topic should be present in the list", (done) => {
    request(api.baseUrl)
      .get("/api/kafka/topics")
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.contain(`${data["kafka_topic"]}`);
        expect(res.body.message).not.to.contain(
          `${data["kakafka_topic_not_present"]}`
        );
        done();
      });
  });

  it("should be able to delete the created topic", (done) => {
    request(api.baseUrl)
      .delete(`/api/kafka/topic/${data["kafka_topic"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.be.equal(
          `Topic ${data["kafka_topic"]} deleted`
        );
        done();
      });
  });

  it("should fail deleting an not present topic", (done) => {
    request(api.baseUrl)
      .delete(`/api/kafka/topic/${data["kakafka_topic_not_present"]}`)
      .set("Accept", "application/json")
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        expect(res.statusCode).to.be.equal(200);
        expect(res.body.message).to.contain(
          `Failed to delete topic ${data["kakafka_topic_not_present"]}`
        );
        done();
      });
  });
});
