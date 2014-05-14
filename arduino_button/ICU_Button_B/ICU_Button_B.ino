
/*
  
  Overview
  
  This button can either be hit quickly or held down.
    - If the button is held down, the computer is asked to toggle consent.
    - If the button is hit, the computer is asked to pause or continue recording.
    
  The higher-level logic is handled by the computer. For example, if we ask the
  computer to continue recording, the computer will only do so if it knows we
  have consent.

*/

// On most boards pin 13 should be used as an output because
// it has an attached LED and an attached resistor. (See
// the digitalWrite() documentation.)

int LED_PIN = 13;
int BUTTON_PIN = 12;

// Times are in milliseconds.
int TOGGLE_CONSENT_TIME = 1000;
int CYCLE_DELAY = 50;

boolean buttonPushed = 0, buttonWasPushed = 0;
int timePushed = 0;
char response;

// Runs once when you hit reset.
void setup() {                
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);   
  pinMode(BUTTON_PIN, INPUT);  
}

void led_on() {
  digitalWrite(LED_PIN, 1);
}

void led_off() {
  digitalWrite(LED_PIN, 0);
}

// on_time is in milliseconds
void blink(int on_time) {
  led_on();
  delay(on_time);
  led_off();
}

void quick_blinks() {
  blink(50);
  delay(300);
  blink(50);
  delay(300);
  blink(50);
}

void long_blink() {
  blink(750);
}

void loop() {
  
  buttonWasPushed = (timePushed > 0);
  buttonPushed = digitalRead(BUTTON_PIN);
  
  // If the button has been pushed for a specific amount of time,
  // we should ask the computer to toggle consent.
  if (timePushed == TOGGLE_CONSENT_TIME) {
    Serial.write('c');
  }
  
  // If the button was pushed and released within a short period of time,
  // we should ask the computer to toggle recording.
  if (buttonWasPushed && !buttonPushed && timePushed < TOGGLE_CONSENT_TIME) {
    Serial.write('r');
  }
  
  // Now let's handle the computer's response. Regardless of whether we asked it to
  // toggle consent or to toggle recording, it will send us back a 0 or a 1.
  // In either case, 0 means off and 1 means on.

  if (Serial.available() > 0) {
    response = Serial.read();
    if (response == '0') {
      quick_blinks();
    }
    else if (response == '1') {
      long_blink();
    }
  }
  
  // Pause this cycle before continuing.
  delay(CYCLE_DELAY);

  // Update timePushed based on this cycle's button status.
  if (buttonPushed) {
    timePushed += CYCLE_DELAY;
  }
  else {
    timePushed = 0;
  }
  
}
