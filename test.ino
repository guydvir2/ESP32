void checkSwitch_PressedDown(){
  bool temp_inputDownPin = digitalRead(inputDownPin);

        if (temp_inputDownPin != inputDown_lastState) {
                delay(deBounceInt);
                if (digitalRead(inputDownPin) != inputDown_lastState) {
                        if (digitalRead(inputDownPin) == LOW && outputDown_currentState!=LOW) {
                                switchIt("Button","down");
                                inputDown_lastState = digitalRead(inputDownPin);
                        }
                        else if (digitalRead(inputDownPin) == HIGH && outputDown_currentState!=HIGH) {
                                switchIt("Button","off");
                                inputDown_lastState = digitalRead(inputDownPin);
                        }
                        else {
                                Serial.println("Wrong command");
                        }
                }
                else {
                  char tMsg [100];
                  sprintf(tMsg,"Down Bounce detected: cRead[%s] lRead[%s]", temp_inputDownPin, inputDown_lastState);
                  pub_msg(tMsg);
                }
        }


}
