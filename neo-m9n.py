from machine import UART, Pin
import time

# Initialize UART0 (Baud rate is 38400 for standard NEO-M9N)
uart = UART(0, baudrate=38400, tx=Pin(0), rx=Pin(1), timeout=1000)

def convert_to_degrees(raw_val, direction):
    """Converts NMEA raw format (DDMM.MMMM) to decimal degrees."""
    if not raw_val:
        return None
    try:
        dot_idx = raw_val.find('.')
        deg_len = dot_idx - 2
        degrees = float(raw_val[:deg_len])
        minutes = float(raw_val[deg_len:])
        decimal = degrees + (minutes / 60.0)
        
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal
    except ValueError:
        return None

def parse_nmea(line):
    """Parses standard GNGGA / GPRMC NMEA sentences from u-blox GNSS."""
    parts = line.split(',')
    sentence_type = parts[0]

    # $GNGGA / $GPGGA: Global Positioning System Fix Data
    if sentence_type in ['$GNGGA', '$GPGGA']:
        if len(parts) >= 10:
            fix_quality = parts[6]
            satellites = parts[7]
            altitude = parts[9]
            lat = convert_to_degrees(parts[2], parts[3])
            lon = convert_to_degrees(parts[4], parts[5])
            
            return {
                'fix': fix_quality != '0' and fix_quality != '',
                'lat': lat,
                'lon': lon,
                'sats': satellites,
                'alt': altitude
            }

    return None

print("Listening for NEO-M9N GPS data...")

try:
    while True:
        if uart.any():
            try:
                line = uart.readline().decode('utf-8', 'ignore').strip()
                parsed = parse_nmea(line)
                
                if parsed and parsed['fix']:
                    print("LAT: {:10.6f} | LON: {:10.6f} | Sats: {:2s} | Alt: {} m".format(
                        parsed['lat'], parsed['lon'], parsed['sats'], parsed['alt']
                    ))
                elif parsed and not parsed['fix']:
                    print("Searching for satellites... (Fix: No)")
            except Exception:
                pass
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")