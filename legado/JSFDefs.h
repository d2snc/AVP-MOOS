/* ---------------------------------------------------------------------- */
/* JSFDefs.h                                                              */
/* ---------------------------------------------------------------------- */
/*                                                                        */
/* (c) Copyright 2006 - 2009, 2011 - 2016, 2017 EdgeTech,                 */
/*                                                                        */
/* This file contains proprietary information, and trade secrets of       */
/* EdgeTech, and may not be disclosed or reproduced without the prior     */
/* written consent of EdgeTech.                                           */
/*                                                                        */
/* EdgeTech is not responsible for the consequences of the use or misuse  */
/* of this software, even if they result from defects in it.              */
/*                                                                        */
/* ---------------------------------------------------------------------- */
/* EdgeTech JSF Data format description.  This is the format that data is */
/* normally stored or transmitted in.  A sonar data message contains a    */
/* 16-byte standard header, followed by the header described here and     */
/* finally followed by the acoustic data.                                 */
/* ---------------------------------------------------------------------- */

#pragma once


/* ---------------------------------------------------------------------- */

#include <stdint.h>


/* ---------------------------------------------------------------------- */
/* Each data record has a 240 byte header, the content of which is defined*/
/* below.  Some fields are redundant such as time stamps, which are       */
/* maintained for backward compatibility.                                 */
/* Non-acoustic fields such as pitch / roll and GPS coordinates, if       */
/* present, are approximate and not normally interpolated to the nearest  */
/* ping time.  Thus, multiple pings may have the same GPS fix.  It is     */
/* highly recommended that the specific messages that contain the         */
/* non-acoustic data be used for this information.  If values are         */
/* interpolated validity flag bit 13 will be set.                         */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time in seconds since 1/1/1970 (standard time() value)   */
  /* Use with (millisecondsToday mod 1000) to get a full time stamp       */
  int32_t    timeSince1970;

  /*   4 -   7 : Starting depth (window offset) in samples.               */
  uint32_t   startDepth;

  /*   8 -  11 : Ping number (increments with ping)                       */
  uint32_t   pingNum;

  /*  12 -  15 : Reserved - do not use                                    */
  int16_t    reserved0[2];

  /*  16 -  17 : Most Significant Bits                                    */
  /* high order bits for fields requiring greater range                   */
  /* Bits  0 -  3 startFreq  - Start Frequency                            */
  /* Bits  4 -  7 endFreq    - End Frequency                              */
  /* Bits  8 - 11 samples    - Samples in this packet                     */
  /* Bits 12 - 15 markNumber - Mark Number                                */
  /* This field was added in protocol version 0xA, and was previously 0   */
  uint16_t   MSB1;

  /*  18 -  19 : LSB - Extended precision                                 */
  /* low order bits for fields requiring greater precision                */
  /* Bits  0 -  7 sampleInterval - Sample interval fractional component   */
  /* Bits  8 - 15 course - fractional portion of course                   */
  /* This field was added in protocol version 0xB, and was previously 0   */
  uint16_t   LSB1;

  /*  20 -  21 : LSB - Extended precision                                 */
  /* low order bits for fields requiring greater precision                */
  /* Bits  0 -  3 speed - sub fractional speed component                  */
  /* This field was added in protocol version 0xC, and was previously 0   */
  /* Bits  4 - 13 sweepLength microsecond portion (0 - 999)               */
  /* This field was added in protocol version 0xD, and was previously 0   */
  uint16_t   LSB2;

  /*  22 -  29 : Reserved - do not use                                    */
  int16_t    reserved1[4];

  /*  30 -  31 : Validity flags bitmap                                    */
  /* Bit  0    : Lat Lon or XY valid                                      */
  /* Bit  1    : Course valid                                             */
  /* Bit  2    : Speed valid                                              */
  /* Bit  3    : Heading valid                                            */
  /* Bit  4    : Pressure valid                                           */
  /* Bit  5    : Pitch roll valid                                         */
  /* Bit  6    : Altitude valid                                           */
  /* Bit  7    : heave valid                                              */
  /* Bit  8    : Water temperature valid                                  */
  /* Bit  9    : Depth valid                                              */
  /* Bit 10    : Annotation valid                                         */
  /* Bit 11    : Cable counter valid                                      */
  /* Bit 12    : KP valid                                                 */
  /* Bit 13    : Position interpolated                                    */
  /* Bit 14    : sound speed valid                                        */
  uint16_t   validityFlags;

  /*  32 -  33 : Reserved - do not use                                    */
  uint16_t   reserved2;

  /*  34 -  35 : DataFormatType                                           */
  /*   0 = 1 short  per sample  - envelope data                           */
  /* the total number of bytes of data to follow is  2 * samples.         */
  /*   1 = 2 shorts per sample  - stored as real(1), imaginary(1),        */
  /* the total number of bytes of data to follow is  4 * samples.         */
  /*   2 = 1 short  per sample  - before matched filter                   */
  /* the total number of bytes of data to follow is  2 * samples.         */
  /*   3 = 1 short  per sample  - real part analytic signal               */
  /* the total number of bytes of data to follow is  2 * samples.         */
  /*   4 = 1 short  per sample  - pixel data / ceros data                 */
  /* the total number of bytes of data to follow is  2 * samples.         */
  /*   5 = 1 byte   per sample  - pixel data                              */
  /* the total number of bytes of data to follow is  1 * samples.         */
  /*   6 = 1 long   per sample  - raw data                                */
  /* the total number of bytes of data to follow is  4 * samples.         */
  /*   7 = 2 floats per sample  - stored as real(1), imaginary(1), - prior*/
  /* to matched filter,                                                   */
  /* the total number of bytes of data to follow is  8 * samples.         */
  /*   8 = 1 float  per sample  - envelope data                           */
  /* the total number of bytes of data to follow is  4 * samples.         */
  /*   9 = 2 shorts per sample  - stored as real(1), imaginary(1), - prior*/
  /* to matched filter,                                                   */
  /* This is the code for unmatchfiltered analytic data whereas value 1   */
  /* is intended for match filtered analytic data.                        */
  /* the total number of bytes of data to follow is  4 * samples.         */
  /*  10 = 1 float  per sample  - before matched filter                   */
  /* the total number of bytes of data to follow is  4 * samples.         */
  /* -----                                                                */
  /* NOTE: Values greater than 255 indicate that the data to follow is    */
  /* compressed and must be decompressed prior to use via the             */
  /* decompression DLL or other means.                                    */
  int16_t    dataFormat;

  /*  36 -  37 : Aft distance from antennae to tow point in cm            */
  int16_t    NMEAantennaeR;

  /*  38 -  39 : Starboard distance from antennae to tow point in cm      */
  int16_t    NMEAantennaeO;

  /*  40 -  43 : Reserved - do not use                                    */
  int16_t    reserved3[2];

  /*  44 -  47 : KP kilometer of pipe (kilometers)                        */
  /* validity flag bit 12                                                 */
  float   kp;

  /*  48 -  51 : Heave in Meters positive down                            */
  /* validity flag bit 7                                                  */
  float   heave;

  /*  52 -  79 : Reserved - do not use                                    */
  int16_t    reserved4[14];

  /* -------------------------------------------------------------------- */
  /* Navigation data :                                                    */
  /* If the coorUnits are seconds(2), the x values represent longitude    */
  /* and the y values represent latitude.  A positive value designates    */
  /* the number of seconds east of Greenwich Meridian or north of the     */
  /* equator.                                                             */
  /* -------------------------------------------------------------------- */

  /*  80 -  83 : Longitude in 10000 * (Minutes of Arc) or X in mm         */
  /* validity flag bit 0                                                  */
  int32_t    groupCoordX;

  /*  84 -  87 : Latitude in 10000 * (Minutes of Arc) or Y in mm          */
  /* validity flag bit 0                                                  */
  int32_t    groupCoordY;

  /*  88 -  89 : Units of coordinates - 1->length mm(x/y), 2->10000 *     */
  /* (Minutes of Arc), 3->length in dm.                                   */
  int16_t    coordUnits;

  /*  90 - 113 : Annotation string                                        */
  int8_t    annotation[24];

  /* 114 - 115 : Samples in this packet                                   */
  /*                                                                      */
  /* Note: For protocol versions 0xA and above, the MSB1 field should     */
  /*       include the MSBS needed to determine the number of samples.    */
  uint16_t   samples;

  /* 116 - 119 : Sample interval in ns of stored data                     */
  /*                                                                      */
  /* Note: For protocol versions 0xB and above, the LSB1 field should     */
  /*       include the fractional component LSBS needed to determine the  */
  /* sample interval.                                                     */
  /*       See field LSB1 for LSBs for increased precision.               */
  uint32_t   sampleInterval;

  /* 120 - 121 : Gain factor of ADC                                       */
  uint16_t   ADCGain;

  /* 122 - 123 : pulse transmit level setting (0 - 100) percent           */
  int16_t    pulsePower;

  /* 124 - 125 : Reserved - do not use                                    */
  int16_t    reserved5;

  /* 126 - 127 : Starting frequency in daHz (10 Hz)                       */
  /* Note: For protocol versions 0xA and above, the MSB1 field should     */
  /*       include the MSBS needed to determine the starting frequency.   */
  uint16_t   startFreq;

  /* 128 - 129 : Ending frequency in daHz (10 Hz)                         */
  /* Note: For protocol versions 0xA and above, the MSB1 field should     */
  /*       include the MSBS needed to determine the ending frequency.     */
  uint16_t   endFreq;

  /* 130 - 131 : Sweep length in ms                                       */
  /* LSB2 bits  4 - 13 contain the microsecond portion (0 - 999)          */
  /* LSB2 part was added in protocol version 0xD, and was previously 0    */
  uint16_t   sweepLength;

  /* 132 - 135 : Pressure in milliPSI - (1/1000 PSI)                      */
  /* validity flag bit 4                                                  */
  int32_t    pressure;

  /* 136 - 139 : Depth estimate in mm                                     */
  /* validity flag bit 9                                                  */
  int32_t    depth;

  /* 140 - 141 : Sample rate in Hz mod 65536                              */
  /* The reciprocal of the sample interval yields better resolution and   */
  /* should be used for all new development.                              */
  /* This field is included for legacy purposes only and is not           */
  /* recommended for new applications.                                    */
  uint16_t   sampleRate;

  /* 142 - 143 : Unique pulse identifier                                  */
  uint16_t   pulseID;

  /* 144 - 147 : Altitude in mm                                           */
  /* validity flag bit 6                                                  */
  int32_t    altitude;

  /* 148 - 151 : sound speed in meters / second                           */
  float   soundSpeed;

  /* 152 - 155 : mixer frequency in Hz                                    */
  /* For single pulse pulses this should be close to the center frequency.*/
  /* For multipulse pulses this should be the approximate center frequency*/
  /* of the span of all the pulses.                                       */
  float   mixerFrequency;

  /* 156 - 157 : Year data recorded (CPU time)                            */
  int16_t    year;

  /* 158 - 159 : day                                                      */
  int16_t    day;

  /* 160 - 161 : hour                                                     */
  int16_t    hour;

  /* 162 - 163 : minute                                                   */
  int16_t    minute;

  /* 164 - 165 : second                                                   */
  int16_t    second;

  /* 166 - 167 : Always 3                                                 */
  int16_t    timeBasis;

  /* 168 - 169 : weighting factor for block floating point expansion      */
  /* -- defined as 2 -N volts for LSB                                     */
  /* IMPORTANT: All data MUST be scaled by pow(2, -weightingFactor)       */
  /*            DO NOT IGNORE THIS VALUE.                                 */
  int16_t    weightingFactor;

  /* 170 - 171 : Number of pulses in the water                            */
  uint8_t   mpxNumPulses;
  uint8_t   mpxCurrentPhase;

  /* -------------------------------------------------------------------- */
  /* From pitch/roll/temp/heading sensor(s)                               */
  /* -------------------------------------------------------------------- */

  /* 172 - 173 : Compass heading  0.00 to 360.00 degrees in 1/100 degree  */
  /* validity flag bit 3                                                  */
  uint16_t   heading;

  /* 174 - 175 : Pitch ((degrees / 180.0) * 32768.0)  maximum resolution  */
  /* -- positive values indicate bow up.                                  */
  /* validity flag bit 5                                                  */
  int16_t    pitch;

  /* 176 - 177 : Roll  ((degrees / 180.0) * 32768.0)  maximum resolution  */
  /* -- positive values indicate port up.                                 */
  /* validity flag bit 5                                                  */
  int16_t    roll;

  /* 178 - 179 : Reserved - do not use                                    */
  int16_t    reserved6;

  /* -------------------------------------------------------------------- */
  /* User defined area from 180-239                                       */
  /* -------------------------------------------------------------------- */

  /* 180 - 181 : Reserved - do not use                                    */
  int16_t    reserved7;

  /* 182 - 183 : TriggerSource (0 = internal, 1 = external, 2 - coupled)  */
  int16_t    trigSource;

  /* 184 - 185 : Mark Number (0 = no mark)                                */
  /* Note: For protocol versions 0xA and above, the MSB1 field should     */
  /*       include the MSBS needed to determine the mark number.          */
  uint16_t   markNumber;

  /* Note that the NMEA time fields are the time of the GPS fix and come  */
  /* from the same sentence which reported the fix.                       */

  /* 186 - 187 : Hour                                                     */
  int16_t    NMEAHour;

  /* 188 - 189 : Minutes                                                  */
  int16_t    NMEAMinutes;

  /* 190 - 191 : Seconds                                                  */
  int16_t    NMEASeconds;

  /* 192 - 193 : Course in degrees                                        */
  /* validity flag bit 1                                                  */
  /* starting with protocol version 0x0C two digits of fractional degrees */
  /* are stored in LSB1                                                   */
  int16_t    NMEACourse;

  /* 194 - 195 : Speed in tenths of a knot                                */
  /* validity flag bit 2                                                  */
  /* starting with protocol version 0x0C one additional digit of          */
  /* fractional knot (1/100) is stored in LSB2                            */
  int16_t    NMEASpeed;

  /* 196 - 197 : Day                                                      */
  /* Note:  Will be 0 if NMEA sentence does not have this field           */
  int16_t    NMEADay;

  /* 198 - 199 : Year                                                     */
  /* Note:  Will be 0 if NMEA sentence does not have this field           */
  int16_t    NMEAYear;

  /* 200 - 203 : Milliseconds today                                       */
  /* Use with seconds since 1970 to get time to the ms                    */
  uint32_t   millisecondsToday;

  /* 204 - 205 : Maximum absolute value of ADC samples for this packet    */
  uint16_t   ADCMax;

  /* 206 - 209 : Reserved - do not use                                    */
  int16_t    reserved8[2];

  /* 210 - 215 : Sonar Software version number                            */
  int8_t    softwareVersion[6];

  /* 216 - 219 : Initial spherical correction factor in samples.          */
  /* A value of -1 indicates that the spherical spreading is disabled.    */
  int32_t    sphericalCorrection;

  /* 220 - 221 : Packet number - Each ping starts with packet 1           */
  uint16_t   packetNum;

  /* 222 - 223 : A/D decimation * 100 before FFT                          */
  int16_t    ADCDecimation;

  /* 224 - 225 : Decimation factor after FFT                              */
  int16_t    decimation;

  /* 226 - 227 : Water Temperature in 1/10 degree C                       */
  /* validity flag bit 8                                                  */
  int16_t    waterTemperature;

  /* 228 - 231 : Distance to the fish in meters                           */
  float   layback;

  /* 232 - 235 : Reserved - do not use                                    */
  int32_t    reserved9;

  /* 236 - 237 : cable out in decimeters                                  */
  /* validity flag bit 11                                                 */
  uint16_t   cableOut;

  /* 238 - 239 : Reserved - do not use                                    */
  uint16_t   reserved10;

  /* -------------------------------------------------------------------- */
  /* Data area begins here                                                */
  /* -------------------------------------------------------------------- */
  /* Data begins at byte 240, has this.samples data points in it          */
  /* Normally : int16_t data[] (see dataFormat field);                    */
  /* -------------------------------------------------------------------- */

} JSFDataType;

/* ---------------------------------------------------------------------- */
/*                       end JSFDefs.h                                    */
/* ---------------------------------------------------------------------- */

