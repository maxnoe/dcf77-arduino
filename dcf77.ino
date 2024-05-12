const int PIN = 2;

bool val = false;
bool high = false;

unsigned long first = 0;
unsigned long start = 0;
unsigned long previous_start = 0;
unsigned long duration = 0;

bool data_bit = false;
int index = 0;

// 59 bits normally, one more during leap seconds
const int n_bits = 60;
bool data[n_bits];


void reset() {
    for (int i=0; i < n_bits; i++) {
        data[i] = false;
    }
    index = 0;
}

void setup() {
    Serial.begin(9600);
    reset();
}

void sendData() {
    Serial.print("data:");
    for (int i=n_bits - 1; i >= 0; i--) {
        Serial.print(data[i]);
    }
    Serial.println();
}

void loop() {
    val = digitalRead(PIN);

    // new pulse starts
    if (!high && val) {
        high = true;

        previous_start = start;
        start = millis();

        if (first == 0) {
            first = start;
        }

        if (previous_start != 0 && (start - previous_start) > 1500) {
            Serial.println("New minute");
            // we got all data
            if (index >= 59) {
                sendData();
            }
            reset();
        }
    } else if (high && !val) {
        high = false;
        duration = millis() - start;
        // 100 ms for 0, 200 ms for 1;
        data_bit = duration > 150;
        data[index] = data_bit;

        Serial.print(start - first);
        Serial.print(" ");
        Serial.print(index);
        Serial.print(" ");
        Serial.println(data_bit);

        index++;
    }
}
