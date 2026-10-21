// on importe les dépendances
const five = require("johnny-five");
const Raspi = require("raspi-io");

// on déclare la board
const board = new five.Board({ io: new Raspi() });

// Une fois la carte prête
board.on("ready", function() {

  // configuration du button de raccrochage du combiné
  var hangupButton = new five.Button({
    pin: "GPIO21",
    isPullup: true,
    holdtime: 10
  });

  // déclenchement lorsque l'on décroche
  hangupButton.on("up", function() {
    board.info("Phone", "PICK UP");
  });

  // déclenchement lorsque l'on raccroche
  hangupButton.on("down", function() {
    board.info("Phone", "HANG UP");
  });
});