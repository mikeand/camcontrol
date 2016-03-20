/* This is gpio_pir, a program for reading a PIR sensor attached
 * to a rasperberry pi.
 * Copyright 2016, Michael Anderson 
 * Licensed under MIT Licence, see LICENCE file for fun facts
*/
#include <stdio.h>
#include <wiringPi.h>

const int PIN_PIR = 7;          // The pin the PIR sensor is attached.
const int PIN_LED = 0;          // The pin the LED output is attached.
const int LATCH_TIME = 30;      // Keep true reading for this many seconds
const int DELAY_MS = 100;       // Number of milliseconds inbetween each  read.
const int CHECK_ENABLED = 5;    // Check if enabled this many seconds
const int LED_BLINK_SECONDS = 60;   // Blink for this many seconds when starting
const int LED_BLINK_WAIT = 500;     // Blink every 500ms
const char* OUT_FILE = "/usr/local/bin/pir";
const char* ENABLE_FILE = "/usr/local/bin/pir_enable";


void outputLatch(bool status) {
    
    if (status) {
        printf("PIR detected movement\n");
	FILE* lock = fopen(OUT_FILE, "w");
        fclose(lock);
    } else {
        printf("Movement not detected for %d seconds, resuming detection.\n", LATCH_TIME);
        remove(OUT_FILE);
    }
}

void blinkLedStartup() {
    int blinkingMs = 0;
    int ledOnOff = 0;

    printf("Blinking for %d seconds not detecting\n", LED_BLINK_SECONDS);
    
    // Blink for a specific number of seconds
    while (blinkingMs < LED_BLINK_SECONDS * 1000) {
        delay(LED_BLINK_WAIT);
        blinkingMs += LED_BLINK_WAIT;
        ledOnOff = 1 - ledOnOff;
        digitalWrite(PIN_LED, ledOnOff);
    }
    // Make sure led is switched off for normal operation
    digitalWrite(PIN_LED, 0);
}

bool isEnabled() {
    FILE *fileNo = fopen(ENABLE_FILE, "r");
    if (fileNo) {
        fclose(fileNo);
    }
    return fileNo != NULL;
}


void detectLoop() {
    int latchTime = 0;
    int checkEnabledTime = 0;
    bool latchStatus = false;
    bool enabled = true;

    blinkLedStartup();

    printf("Starting detection\n");

    while (enabled) {
        int pirStatus = digitalRead(PIN_PIR);
        delay(DELAY_MS);

        // PIR has been activated
        if (pirStatus != 0) {
            latchTime = 0;

            if (!latchStatus) {
                latchStatus = true;
                outputLatch(true);
            }
        }

        // When latched it stays latched for a number
        // of seconds before resetting back.
        if (latchStatus) {
            latchTime += DELAY_MS;
        if (latchTime >= 1000 * LATCH_TIME) {
            latchStatus = false;
            outputLatch(false);
            }
        }

        // Check enabled only after time has passed.
        if (checkEnabledTime >= 1000 * CHECK_ENABLED) {
            enabled = isEnabled();
            checkEnabledTime = 0;
        }
    }
}




#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wmissing-noreturn"
int main() {
    bool enabled = isEnabled();

    printf("Raspberry Pi Pir Checker\n");

    if (wiringPiSetup() == -1) {
        fprintf(stderr, "Cannot setup GPIO\n");
        return 1;
    }

    pinMode(PIN_PIR, INPUT);
    pinMode(PIN_LED, OUTPUT);

    while (true) {
        if (enabled) {
            enabled = isEnabled();
            delay(1000 * CHECK_ENABLED);
        } else {
            detectLoop();
        }
    }
}
#pragma clang diagnostic pop
