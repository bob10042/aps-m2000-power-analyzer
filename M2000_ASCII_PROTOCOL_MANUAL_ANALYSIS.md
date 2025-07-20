# M2000 ASCII Protocol - Manual Analysis

## ✅ **Official Confirmation from M2000 Manual**

### **Key Quote from Manual Section 10 (Remote Control Programming):**

> *"The protocol used for communications is entirely ASCII based, using the commonly used **command and data fields approach although not SCPI**. The same protocol is used for all interfaces."*

This **officially confirms** that:
1. ❌ **NOT SCPI protocol**
2. ✅ **ASCII-based proprietary protocol**
3. ✅ **Command and data fields approach**
4. ✅ **Same protocol for RS232, LAN, and USB**

## **ASCII Command Structure (Manual Section 10.4)**

### **Character Set and Encoding:**
- **7-bit ASCII character set** using 8-bit encoding (8th bit is zero)
- Independent of actual interface being used
- Commands are streams of characters

### **Command Format:**
```
KEYWORD [field1] [field2] [field3] ...
```

**Quote from Manual**: *"Each command is a KEYWORD field defining the command, possibly followed by further fields that refine the action of the command."*

### **Special Characters:**

1. **Command Terminators**: LF, CR, FF, or NULL (0 value)
2. **Command Separators**: Semicolon (`;`) between multiple commands
3. **Field Separators**: Comma (`,`) between fields
4. **Sub-field Separators**: Colon (`:`) between sub-fields within a field
5. **Whitespace**: Space, tab, underscore for readability (optional)

### **Command Sets:**
- Multiple commands can be in a single command set
- Separated by semicolons: `command1;command2;command3`
- If error found, that command and all following commands are not executed
- Maximum 4095 characters per command set

## **RDEF Field Structure (Manual Section 10.5.10)**

### **READ Command Syntax:**
The READ command uses RDEF (READ Definition) fields with **up to 5 sub-fields**:

```
READ?,MEASUREMENT_DATA:MEASUREMENT_SOURCE:2ND_SOURCE:MEASUREMENT_TYPE:ENDING_HARMONIC
```

### **Sub-Field Details:**

#### **1. Measurement Data (KEYWORD)**
**Available Parameters:**
- `FREQ` - Signal frequency (Hz)
- `PERIOD` - Signal period (seconds)
- `INTEGTIME` - Integration time (Hours)
- `VOLTS` or `V` - Voltage (V)
- `VPH-PH` - Inter-phase voltage (V)
- `AMPS` or `A` - Current (A) **[DEFAULT]**
- `WATTS` or `W` - Real power (W)
- `LOSS` - Real power loss (W)
- `EFFICIENCY` or `EFF` - Efficiency (%)
- `VAR` - Imaginary power (W)
- `VA` - Apparent power (VA)
- `PF` - Power factor
- `PHASE` - Apparent phase (degrees)
- `LOADZ`/`ZLOAD` - Load impedance (ohms)
- And many others...

#### **2. Measurement Source (KEYWORD)**
**Channel Sources:**
- `CH1`, `CH2`, `CH3`, `CH4` - Individual channels **[CH1 is DEFAULT]**
- `A1`, `A2`, `A3` - VPA aliases
- `VPA1`, `VPA2`, `VPA3` - Virtual Power Analyzers
- `MOTOR` - Motor measurement result
- `IN`, `MIDDLE`, `OUT` - Efficiency groups

#### **3. 2nd Measurement Source (KEYWORD)**
- `MIDDLE`, `OUT` - For efficiency calculations
- `pA`, `pB`, `pC`, `pD` - Individual VPA channels
- `pAC`, `pAB`, `pBC` - Phase-to-phase voltages
- `pN` - Neutral current
- `WYE`, `DELTA` - Wye/Delta voltages

#### **4. Measurement Type (KEYWORD)**
**Coupling Types:**
- `DC` - DC component only
- `AC` - AC component only
- `ACDC` or `RMS` - AC+DC RMS measurement **[DEFAULT]**
- `COUPLED` - Coupled measurement

**Statistical Types:**
- `PK` - Peak value
- `VALLEY` - Valley peak
- `CF` - Crest factor
- `AVERAGE` - Average value

**Sequence Components:**
- `SEQZERO` - Zero sequence
- `SEQPOS` - Positive sequence
- `SEQNEG` - Negative sequence

#### **5. Ending Harmonic (NR1)**
- `H1` to `H500` - Harmonic number for harmonic analysis
- `P1` to `P500` - Phase of specific harmonic

## **Practical Command Examples:**

### **Basic Measurements:**
```
READ?,VOLTS:CH1:ACDC          # Channel 1 voltage (AC+DC RMS)
READ?,AMPS:CH2:AC             # Channel 2 current (AC only)
READ?,WATTS:VPA1              # VPA1 total power
READ?,FREQ:CH1                # Channel 1 frequency
READ?,PF:VPA1                 # VPA1 power factor
```

### **Multiple Commands:**
```
READ?,VOLTS:CH1;READ?,AMPS:CH1;READ?,WATTS:CH1
```

### **Harmonic Analysis:**
```
READ?,VOLTS:CH1:H1            # Fundamental voltage
READ?,AMPS:CH1:H3             # 3rd harmonic current
READ?,VOLTS:CH1:THDF          # Total harmonic distortion
```

### **3-Phase Measurements:**
```
READ?,WATTS:VPA1              # Total 3-phase power
READ?,VOLTS:CH1:pAB:VPA1     # Phase A-B voltage
READ?,AMPS:CH1:pN:VPA1       # Neutral current
```

## **Command vs Query Distinction:**

### **Commands (No Response):**
- `*RST` - Reset device
- `*CLS` - Clear device
- `LOCAL` - Return to local control
- `LOCKOUT` - Enter lockout state

### **Queries (Return Response):**
- `*IDN?` - Device identification
- `*ERR?` - Error status
- `READ?,field` - Measurement data
- `REREAD?` - Repeat last READ
- `CHNL?,channel` - Channel information

## **Response Format (NR3):**

**Fixed 11-character floating-point format:**
```
+1.23456E+3  (= 1234.56)
-9.87654E-2  (= -0.0987654)
+0.00000E+0  (= data unavailable)
```

**Special Cases:**
- `+0.00000E-9` = actual zero value
- `+0.00000E+0` = data unavailable/invalid

## **Error Handling:**

**Error Register (*ERR? query) Values:**
- `0` - No error
- `1` - Command cannot be executed at this time
- `2` - Content/configuration not compatible
- `3` - Data field out of valid range
- `4` - Invalid field syntax
- `5` - Expected field missing
- `6` - Unexpected field found
- `7` - Invalid interface command
- `8` - Response data too many characters
- `9` - Response requested but previous not read
- `10` - Rx overrun occurred

## **Implementation Notes:**

1. **Case Insensitive**: All commands and keywords
2. **Sub-field Order**: Can be specified in any order
3. **Optional Fields**: Can be omitted (defaults used)
4. **Whitespace**: Can be used for readability
5. **Character Streaming**: M2000 stores until terminator received
6. **Error Recovery**: Use *ERR? query for debugging

This comprehensive analysis confirms that the M2000 uses a sophisticated ASCII-based command protocol with a well-defined field structure, completely separate from SCPI standards.