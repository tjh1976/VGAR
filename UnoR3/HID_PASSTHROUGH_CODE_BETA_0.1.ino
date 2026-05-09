#define SHIFT 0x80
// Define CAPS LOCK handling for Atari
#define HID_KEY_CAPS_LOCK 0x39
// Define the ASCII keymap for regular characters
// Format: [ASCII] = HID code

uint8_t buf[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };

void setup() {
 Serial.begin(9600);
}


void loop() {
  if (Serial.available() >= 2) {
    uint8_t modifier = Serial.read();
    uint8_t keycode  = Serial.read();

    sendKey(modifier, keycode);
  }
}


void sendKey(uint8_t modifier, uint8_t keycode) {
  delay(5);

  buf[0] = modifier;  // <-- NOW USED
  buf[2] = keycode;

  Serial.write(buf, 8);  // key press

  //delay(5);

  //buf[0] = 0;
  //buf[2] = 0;

  //Serial.write(buf, 8);  // key release
}






