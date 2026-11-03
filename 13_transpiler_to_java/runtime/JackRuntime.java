/** Runtime for generated Jack programs. No external Java dependencies. */
public final class JackRuntime {
    private JackRuntime() {}

    private static final int[] ram = new int[32768];
    private static final java.util.TreeMap<java.lang.Integer, java.lang.Integer> free = new java.util.TreeMap<>();
    private static final java.util.Map<java.lang.Integer, java.lang.Integer> allocated = new java.util.HashMap<>();
    private static final java.io.BufferedReader input = new java.io.BufferedReader(
        new java.io.InputStreamReader(java.lang.System.in, java.nio.charset.StandardCharsets.UTF_8));

    static {
        free.put(2048, 16384 - 2048);
    }

    public static boolean truth(int word) {
        return word != 0;
    }

    private static void check(boolean valid, java.lang.String message) {
        if (!valid) throw new java.lang.IllegalArgumentException(message);
    }

    public static int peek(int address) {
        check(address >= 0 && address < ram.length, "Invalid RAM address: " + address);
        return ram[address];
    }

    public static int poke(int address, int value) {
        check(address >= 0 && address < ram.length, "Invalid RAM address: " + address);
        ram[address] = (short) value;
        return 0;
    }

    public static int literal(java.lang.String text,
                              java.util.function.IntUnaryOperator create,
                              java.util.function.IntBinaryOperator append) {
        int result = create.applyAsInt(text.length());
        for (int index = 0; index < text.length(); index++) {
            result = append.applyAsInt(result, (short) text.charAt(index));
        }
        return result;
    }

    private static final class Halt extends java.lang.RuntimeException {
        private Halt() { super(null, null, false, false); }
    }

    public static void run(java.util.function.IntSupplier entry) {
        try {
            entry.getAsInt();
        } catch (Halt halt) {
            // Sys.halt terminates the Jack entry point normally.
        }
    }

    public static final class Memory {
        public static int j_init() {
            java.util.Arrays.fill(ram, 0);
            allocated.clear();
            free.clear();
            free.put(2048, 16384 - 2048);
            return 0;
        }

        public static int j_peek(int address) { return peek(address); }
        public static int j_poke(int address, int value) { return poke(address, value); }

        public static int j_alloc(int size) {
            check(size >= 0, "Negative allocation size");
            size = java.lang.Math.max(size, 1);
            for (java.util.Map.Entry<java.lang.Integer, java.lang.Integer> block : free.entrySet()) {
                int address = block.getKey(), available = block.getValue();
                if (available < size) continue;
                free.remove(address);
                if (available > size) free.put(address + size, available - size);
                allocated.put(address, size);
                java.util.Arrays.fill(ram, address, address + size, 0);
                return address;
            }
            throw new java.lang.IllegalStateException("Jack heap exhausted");
        }

        public static int j_deAlloc(int address) {
            java.lang.Integer size = allocated.remove(address);
            check(size != null, "Invalid or already freed allocation: " + address);
            java.util.Map.Entry<java.lang.Integer, java.lang.Integer> previous = free.lowerEntry(address);
            if (previous != null && previous.getKey() + previous.getValue() == address) {
                size += previous.getValue();
                free.remove(previous.getKey());
                address = previous.getKey();
            }
            java.lang.Integer following = free.remove(address + size);
            if (following != null) size += following;
            free.put(address, size);
            return 0;
        }
    }

    public static final class Array {
        public static int j_new(int size) { return Memory.j_alloc(size); }
        public static int j_dispose(int self) { return Memory.j_deAlloc(self); }
    }

    public static final class Math {
        public static int j_init() { return 0; }
        public static int j_abs(int value) { return (short) java.lang.Math.abs(value); }
        public static int j_multiply(int left, int right) { return (short) (left * right); }
        public static int j_divide(int left, int right) { return (short) (left / right); }
        public static int j_min(int left, int right) { return java.lang.Math.min(left, right); }
        public static int j_max(int left, int right) { return java.lang.Math.max(left, right); }
        public static int j_sqrt(int value) {
            check(value >= 0, "Cannot take square root of a negative word");
            return (int) java.lang.Math.sqrt(value);
        }
    }

    public static final class String {
        // Object fields: chars (Array), capacity, length.
        public static int j_new(int capacity) {
            check(capacity >= 0, "Negative string capacity");
            int self = Memory.j_alloc(3);
            poke(self, Array.j_new(capacity));
            poke(self + 1, capacity);
            return self;
        }

        public static int j_dispose(int self) {
            Array.j_dispose(peek(self));
            return Memory.j_deAlloc(self);
        }

        public static int j_length(int self) { return peek(self + 2); }

        private static int characterAddress(int self, int index) {
            check(index >= 0 && index < j_length(self), "String index out of range");
            return peek(self) + index;
        }

        public static int j_charAt(int self, int index) { return peek(characterAddress(self, index)); }
        public static int j_setCharAt(int self, int index, int character) {
            return poke(characterAddress(self, index), character);
        }

        public static int j_appendChar(int self, int character) {
            int length = j_length(self);
            check(length < peek(self + 1), "String capacity exceeded");
            poke(peek(self) + length, character);
            poke(self + 2, length + 1);
            return self;
        }

        public static int j_eraseLastChar(int self) {
            int length = j_length(self);
            check(length > 0, "Cannot erase an empty string");
            poke(peek(self) + length - 1, 0);
            return poke(self + 2, length - 1);
        }

        public static int j_intValue(int self) {
            int index = 0, sign = 1, result = 0;
            if (j_length(self) > 0 && j_charAt(self, 0) == '-') {
                sign = -1;
                index++;
            }
            while (index < j_length(self)) {
                int digit = j_charAt(self, index++) - '0';
                if (digit < 0 || digit > 9) break;
                result = (short) (result * 10 + digit);
            }
            return (short) (sign * result);
        }

        public static int j_setInt(int self, int value) {
            java.lang.String text = java.lang.Integer.toString((short) value);
            check(text.length() <= peek(self + 1), "String capacity exceeded");
            poke(self + 2, 0);
            for (int index = 0; index < text.length(); index++) j_appendChar(self, text.charAt(index));
            return 0;
        }

        public static int j_newLine() { return 128; }
        public static int j_backSpace() { return 129; }
        public static int j_doubleQuote() { return 34; }
    }

    public static final class Output {
        public static int j_init() { return 0; }

        public static int j_moveCursor(int row, int column) {
            check(row >= 0 && row < 23 && column >= 0 && column < 64, "Invalid output cursor");
            java.lang.System.out.print("\033[" + (row + 1) + ";" + (column + 1) + "H");
            return 0;
        }

        public static int j_printChar(int character) {
            if (character == 128) return j_println();
            if (character == 129) return j_backSpace();
            java.lang.System.out.print((char) character);
            java.lang.System.out.flush();
            return 0;
        }

        public static int j_printString(int text) {
            for (int index = 0; index < String.j_length(text); index++) {
                j_printChar(String.j_charAt(text, index));
            }
            return 0;
        }

        public static int j_printInt(int value) {
            java.lang.System.out.print((short) value);
            java.lang.System.out.flush();
            return 0;
        }

        public static int j_println() {
            java.lang.System.out.println();
            return 0;
        }

        public static int j_backSpace() {
            java.lang.System.out.print("\b \b");
            java.lang.System.out.flush();
            return 0;
        }
    }

    public static final class Keyboard {
        public static int j_init() { return 0; }
        public static int j_keyPressed() { return peek(24576); }

        public static int j_readChar() {
            try {
                int character = input.read();
                if (character < 0) return 0;
                if (character == '\r') {
                    input.mark(1);
                    if (input.read() != '\n') input.reset();
                    return 128;
                }
                if (character == '\n') return 128;
                return character == 8 || character == 127 ? 129 : (short) character;
            } catch (java.io.IOException error) {
                throw new java.io.UncheckedIOException(error);
            }
        }

        public static int j_readLine(int message) {
            Output.j_printString(message);
            try {
                java.lang.String line = input.readLine();
                if (line == null) line = "";
                return literal(line, String::j_new, String::j_appendChar);
            } catch (java.io.IOException error) {
                throw new java.io.UncheckedIOException(error);
            }
        }

        public static int j_readInt(int message) {
            int line = j_readLine(message);
            int value = String.j_intValue(line);
            String.j_dispose(line);
            return value;
        }
    }

    /** Headless screen: drawing updates the Hack screen words in RAM. */
    public static final class Screen {
        private static boolean black = true;
        public static int j_init() { black = true; return j_clearScreen(); }
        public static int j_clearScreen() { java.util.Arrays.fill(ram, 16384, 24576, 0); return 0; }
        public static int j_setColor(int color) { black = truth(color); return 0; }

        public static int j_drawPixel(int x, int y) {
            check(x >= 0 && x < 512 && y >= 0 && y < 256, "Pixel outside screen");
            int address = 16384 + y * 32 + x / 16;
            int mask = 1 << (x % 16);
            return poke(address, black ? peek(address) | mask : peek(address) & ~mask);
        }

        public static int j_drawLine(int x1, int y1, int x2, int y2) {
            check(x1 >= 0 && x1 < 512 && x2 >= 0 && x2 < 512
                && y1 >= 0 && y1 < 256 && y2 >= 0 && y2 < 256, "Line outside screen");
            int dx = java.lang.Math.abs(x2 - x1), dy = -java.lang.Math.abs(y2 - y1);
            int sx = x1 < x2 ? 1 : -1, sy = y1 < y2 ? 1 : -1, error = dx + dy;
            while (true) {
                j_drawPixel(x1, y1);
                if (x1 == x2 && y1 == y2) return 0;
                int doubled = 2 * error;
                if (doubled >= dy) { error += dy; x1 += sx; }
                if (doubled <= dx) { error += dx; y1 += sy; }
            }
        }

        public static int j_drawRectangle(int x1, int y1, int x2, int y2) {
            check(x1 >= 0 && x1 <= x2 && x2 < 512 && y1 >= 0 && y1 <= y2 && y2 < 256,
                "Invalid rectangle");
            for (int y = y1; y <= y2; y++) j_drawLine(x1, y, x2, y);
            return 0;
        }

        public static int j_drawCircle(int x, int y, int radius) {
            check(radius >= 0 && radius <= 181 && x - radius >= 0 && x + radius < 512
                && y - radius >= 0 && y + radius < 256, "Invalid circle");
            for (int offset = -radius; offset <= radius; offset++) {
                int span = (int) java.lang.Math.sqrt(radius * radius - offset * offset);
                j_drawLine(x - span, y + offset, x + span, y + offset);
            }
            return 0;
        }
    }

    public static final class Sys {
        public static int j_init() {
            Memory.j_init(); Math.j_init(); Screen.j_init(); Output.j_init(); Keyboard.j_init();
            return 0;
        }
        public static int j_halt() { throw new Halt(); }
        public static int j_wait(int duration) {
            check(duration >= 0, "Negative wait duration");
            try {
                java.lang.Thread.sleep(duration);
            } catch (java.lang.InterruptedException error) {
                java.lang.Thread.currentThread().interrupt();
                throw new java.lang.IllegalStateException("Jack wait interrupted", error);
            }
            return 0;
        }
        public static int j_error(int code) { throw new java.lang.IllegalStateException("ERR" + code); }
    }
}
