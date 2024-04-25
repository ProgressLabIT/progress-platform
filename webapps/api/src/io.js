const createSocket = (server, consumer) => {
  const io = require("socket.io")(server);

  // Handle Socket connections
  io.on("connection", (socket) => {
    console.log(`--> JOINED: ${socket.id}`);

    // Handle serial create Event
    socket.on("serial create", (data) => {
      console.log(`\n    SERIAL CREATE:   ${socket.id} -- ${data}`);
      //TODO: emit on kafka
    });

    return io;
  });

  // Listen for Kafka
  consumer.on("message", ({ value }) => {
    // Parse the JSON value into an object
    const { payload } = JSON.parse(value);

    // Get the properties from the update
    const { properties } = payload.after;

    // ... and the status
    const { status } = properties;

    console.log("\n\nemitting from kafka:", status, properties);

    // Emit the message through all connected sockets
    io.emit(status, properties);
  });
};

module.exports = createSocket;
