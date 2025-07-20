#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - Unit Formatting Helper
Provides proper unit display and scaling for M2000 measurement data
"""

def format_measurement(value, parameter, include_units=True):
    """
    Format measurement value with appropriate units and scaling
    
    Args:
        value: Numeric value from M2000 (in native units)
        parameter: Parameter type (V, A, W, VA, VAR, PF, FREQ, PHASE, etc.)
        include_units: Whether to include unit suffix
    
    Returns:
        Formatted string with value and units
    """
    if value is None or value == 0.0:
        if include_units:
            return f"0.000 {get_base_unit(parameter)}"
        return "0.000"
    
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    # Handle special parameters without units
    if parameter in ['PF']:  # Power Factor is dimensionless
        return f"{val:.4f}"
    
    if parameter in ['PHASE']:  # Phase in degrees
        return f"{val:.2f}°" if include_units else f"{val:.2f}"
    
    # Get base unit
    base_unit = get_base_unit(parameter)
    
    # Auto-scale based on magnitude
    abs_val = abs(val)
    
    if parameter in ['V']:  # Voltage scaling
        if abs_val >= 1000:
            return f"{val/1000:.3f} kV" if include_units else f"{val/1000:.3f}"
        elif abs_val >= 1:
            return f"{val:.3f} V" if include_units else f"{val:.3f}"
        elif abs_val >= 0.001:
            return f"{val*1000:.1f} mV" if include_units else f"{val*1000:.1f}"
        elif abs_val >= 0.000001:
            return f"{val*1000000:.0f} μV" if include_units else f"{val*1000000:.0f}"
        else:
            return f"{val*1000000000:.0f} nV" if include_units else f"{val*1000000000:.0f}"
    
    elif parameter in ['A']:  # Current scaling  
        if abs_val >= 1000:
            return f"{val/1000:.3f} kA" if include_units else f"{val/1000:.3f}"
        elif abs_val >= 1:
            return f"{val:.3f} A" if include_units else f"{val:.3f}"
        elif abs_val >= 0.001:
            return f"{val*1000:.1f} mA" if include_units else f"{val*1000:.1f}"
        elif abs_val >= 0.000001:
            return f"{val*1000000:.0f} μA" if include_units else f"{val*1000000:.0f}"
        else:
            return f"{val*1000000000:.0f} nA" if include_units else f"{val*1000000000:.0f}"
    
    elif parameter in ['W']:  # Power scaling
        if abs_val >= 1000000:
            return f"{val/1000000:.3f} MW" if include_units else f"{val/1000000:.3f}"
        elif abs_val >= 1000:
            return f"{val/1000:.3f} kW" if include_units else f"{val/1000:.3f}"
        elif abs_val >= 1:
            return f"{val:.3f} W" if include_units else f"{val:.3f}"
        elif abs_val >= 0.001:
            return f"{val*1000:.1f} mW" if include_units else f"{val*1000:.1f}"
        elif abs_val >= 0.000001:
            return f"{val*1000000:.0f} μW" if include_units else f"{val*1000000:.0f}"
        else:
            return f"{val*1000000000:.0f} nW" if include_units else f"{val*1000000000:.0f}"
    
    elif parameter in ['VA', 'VAR']:  # Apparent/Reactive power scaling (same as W)
        if abs_val >= 1000000:
            return f"{val/1000000:.3f} M{base_unit}" if include_units else f"{val/1000000:.3f}"
        elif abs_val >= 1000:
            return f"{val/1000:.3f} k{base_unit}" if include_units else f"{val/1000:.3f}"
        elif abs_val >= 1:
            return f"{val:.3f} {base_unit}" if include_units else f"{val:.3f}"
        elif abs_val >= 0.001:
            return f"{val*1000:.1f} m{base_unit}" if include_units else f"{val*1000:.1f}"
        elif abs_val >= 0.000001:
            return f"{val*1000000:.0f} μ{base_unit}" if include_units else f"{val*1000000:.0f}"
        else:
            return f"{val*1000000000:.0f} n{base_unit}" if include_units else f"{val*1000000000:.0f}"
    
    elif parameter in ['FREQ']:  # Frequency scaling
        if abs_val >= 1000000:
            return f"{val/1000000:.3f} MHz" if include_units else f"{val/1000000:.3f}"
        elif abs_val >= 1000:
            return f"{val/1000:.3f} kHz" if include_units else f"{val/1000:.3f}"
        else:
            return f"{val:.3f} Hz" if include_units else f"{val:.3f}"
    
    else:
        # Default formatting for unknown parameters
        if include_units and base_unit:
            return f"{val:.6g} {base_unit}"
        return f"{val:.6g}"


def get_base_unit(parameter):
    """Get the base unit for a parameter"""
    unit_map = {
        'V': 'V',
        'A': 'A', 
        'W': 'W',
        'VA': 'VA',
        'VAR': 'VAR',
        'PF': '',
        'FREQ': 'Hz',
        'PHASE': '°',
        'THDF': '%',
        'THDSIG': '%',
        'CF': '',
        'FF': '',
    }
    return unit_map.get(parameter, '')


def format_measurement_table(data_dict, title="Measurements"):
    """
    Format measurement dictionary as a readable table
    
    Args:
        data_dict: Dictionary with measurement data {channel_param: value}
        title: Table title
    
    Returns:
        Formatted string table
    """
    if not data_dict:
        return f"{title}: No data"
    
    lines = [f"\n{title}:"]
    lines.append("-" * (len(title) + 1))
    
    # Group by channel
    channels = {}
    for key, value in data_dict.items():
        if '_' in key:
            channel, param = key.split('_', 1)
            if channel not in channels:
                channels[channel] = {}
            channels[channel][param] = value
    
    # Format each channel
    for channel in sorted(channels.keys()):
        lines.append(f"\n{channel}:")
        for param in sorted(channels[channel].keys()):
            value = channels[channel][param]
            formatted = format_measurement(value, param, include_units=True)
            lines.append(f"  {param:>6}: {formatted:>12}")
    
    return '\n'.join(lines)


def create_csv_header(channels, parameters):
    """Create CSV header with units"""
    header = "Timestamp"
    for param in parameters:
        for channel in channels:
            unit = get_base_unit(param)
            if unit:
                header += f",{channel}_{param}({unit})"
            else:
                header += f",{channel}_{param}"
    return header


def format_csv_row(timestamp, data_dict, channels, parameters):
    """Format CSV row with properly scaled values"""
    row = f"{timestamp:.3f}"
    for param in parameters:
        for channel in channels:
            key = f"{channel}_{param}"
            value = data_dict.get(key, '')
            if value != '':
                try:
                    # For CSV, use raw values but format consistently
                    row += f",{float(value):.6g}"
                except (ValueError, TypeError):
                    row += f",{value}"
            else:
                row += ","
    return row


# Example usage and testing
if __name__ == "__main__":
    # Test data (typical M2000 responses)
    test_data = {
        'CH1_V': 230.45,          # 230.45 V
        'CH1_A': 0.001234,        # 1.234 mA  
        'CH1_W': 0.009255,        # 9.255 mW
        'CH1_VA': 0.284,          # 284 mVA
        'CH1_PF': 0.032,          # 0.032 (dimensionless)
        'CH1_FREQ': 50.0,         # 50.0 Hz
        'CH2_V': 0.000450,        # 450 μV
        'CH2_A': 0.000000038,     # 38 nA
        'CH2_W': 1250.5,          # 1.25 kW
        'VPA1_W': 1500000.0,      # 1.5 MW
    }
    
    print("=== Unit Formatting Test ===")
    for key, value in test_data.items():
        channel, param = key.split('_')
        formatted = format_measurement(value, param)
        print(f"{key:>10}: {value:>12g} -> {formatted:>15}")
    
    print(format_measurement_table(test_data, "Test Measurements"))
    
    print("\n=== CSV Header Test ===")
    header = create_csv_header(['CH1', 'CH2'], ['V', 'A', 'W'])
    print(header)
    
    print("\n=== CSV Row Test ===") 
    row = format_csv_row(1.234, test_data, ['CH1', 'CH2'], ['V', 'A', 'W'])
    print(row)