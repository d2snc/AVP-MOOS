/* ---------------------------------------------------------------------- */
/* InterfaceMessages.h                                                    */
/* ---------------------------------------------------------------------- */
/*                                                                        */
/* Describes the standard sonar messages used to communicate with the     */
/* EdgeTech public interface.  Messages always consist of 2 parts:        */
/*      1) A header which contains the message type and length            */
/*      2) The actual data                                                */
/*                                                                        */
/* Note that two communications circuits (TCP sockets) are used.          */
/* One socket is used for commands and the other socket is used for data. */
/*                                                                        */
/* ---------------------------------------------------------------------- */
/*                                                                        */
/* (c) Copyright 2015 - 2017 EdgeTech                                      */
/*                                                                        */
/* All rights reserved.                                                   */
/* This file contains proprietary information, and trade secrets of       */
/* EdgeTech, and may not be disclosed or reproduced without the prior     */
/* written consent of EdgeTech.                                           */
/*                                                                        */
/* EdgeTech is not responsible for the consequences of the use or misuse  */
/* of this software, even if they result from defects in it.              */
/*                                                                        */
/* This information may change without notice.                            */
/* ---------------------------------------------------------------------- */

#pragma once

/* ---------------------------------------------------------------------- */
/* Includes                                                               */
/* ---------------------------------------------------------------------- */

#include <stdint.h>


/* ---------------------------------------------------------------------- */
/* Structure defines                                                      */
/* ---------------------------------------------------------------------- */

#define FILE_NAME_SIZE                       (80)
#define SONAR_MESSAGE_STRING_LENGTH         (256)
#define PING_LIST_SIZE                       (30)


/* ---------------------------------------------------------------------- */
/*  Message Header                                                        */
/* ---------------------------------------------------------------------- */
/* All messages are preceded with a header which indicates the size of    */
/* the message to follow in bytes and its type.  The header is of type    */
/* SonarMessageHeaderType. A version number is included to accommodate    */
/* future changes / extensions in the protocol.                           */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /* Marker for the start of header                                       */
  uint16_t startOfMessage;

  /* The version of the protocol in use                                   */
  uint8_t version;

  /* Session Identifier                                                   */
  uint8_t sessionID;

  /* The message format as per SonarMessageType                           */
  uint16_t sonarMessage;

  /* The action to perform as per SonarCommandType                        */
  uint8_t sonarCommand;

  /* Indicates subsystem (0 is first) for a multi-system device.          */
  uint8_t subSystem;

  /* Indicates channel (0 is first) for a multi-channel subsystem.        */
  uint8_t channel;

  /* Sequence number of message.  A reply to this message will contain    */
  /* this value.  A topside can optionally use this field to track replies*/
  uint8_t sequence;

  /* Header space reserved for future use.                                */
  uint8_t reservedHeader[2];

  /* Size of message in bytes to follow                                   */
  int32_t byteCount;

}  SonarMessageHeaderType;


/* ---------------------------------------------------------------------- */
/* Header defines                                                         */
/* ---------------------------------------------------------------------- */

/* Start of header word                                                   */
#define SONAR_MESSAGE_HEADER_START         (0x1601)

/* The version of the protocol in use                                     */
#define SONAR_PROTOCOL_CURRENT_VERSION       (0x10)


/* ---------------------------------------------------------------------- */
/* Command Types                                                          */
/* ---------------------------------------------------------------------- */
/* Command type(sonarCommand in header).  A topside will send SET         */
/* commands, which return no values, GET commands, which return the       */
/* current parameter set.  The bottom unit only sends REPLY messages in   */
/* response to a GET or unsolicited data.                                 */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* Send a value or execute a command                                    */
  SONAR_COMMAND_SET = 0,

  /* Request current value / last value of item.  All GETs can be sent    */
  /* with a byte count of 0.  Some GET messages will accept parameters.   */
  /* See the individual message descriptions for details.                 */
  SONAR_COMMAND_GET,

  /* Reply to a COMMAND_GET or unsolicited error messages                 */
  SONAR_COMMAND_REPLY,

  /* Error replay to a command.  The command was not executed.            */
  /* In this case, the return value is the error (SonarMessageLongType)   */
  /* as defined by SonarMessageErrorType.                                 */
  SONAR_COMMAND_ERROR,

  /* Similar to a REPLY for the data socket, but is playback data.  This  */
  /* will only occur when storage playback is enabled.                    */
  SONAR_COMMAND_PLAYBACK,

  /* Similar to a REPLY for the data socket, but is QC data.  This will   */
  /* only occur when QC data is enabled.                                  */
  SONAR_COMMAND_QUALITY,

}  SonarCommandType;


/* ---------------------------------------------------------------------- */
/* Error codes that can be returned as SONAR_COMMAND_ERROR                */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* 0: No error                                                          */
  SONAR_MESSAGE_ERROR_NONE = 0,

  /* 1: General command failure indicator                                 */
  SONAR_MESSAGE_ERROR_FAILED,

  /* 2: Message size does not match expected size                         */
  SONAR_MESSAGE_ERROR_DATA_SIZE,

  /* 3: Subsystem number is not currently valid for this command          */
  SONAR_MESSAGE_ERROR_SUBSYSTEM,

  /* 4: Channel number is not currently valid for this command            */
  SONAR_MESSAGE_ERROR_CHANNEL,

  /* 5: sonarMessage field contains an unknown command                    */
  SONAR_MESSAGE_ERROR_UNKNOWN,

  /* 6: Pulse file error.  Pulse not loaded                               */
  SONAR_MESSAGE_ERROR_PULSE_FILE,

}  SonarMessageErrorType;


/* ---------------------------------------------------------------------- */
/* Specific Subsystem Numbers                                             */
/* ---------------------------------------------------------------------- */

/* Sub-Bottom single frequency                                            */
#define SUBSYSTEM_SUB_BOTTOM                               0

/* Side Scan Low Frequency (single frequency or the lowest in system)     */
#define SUBSYSTEM_SIDESCAN_SSL                            20

/* Side Scan High Frequency (higher than the low frequency)               */
#define SUBSYSTEM_SIDESCAN_SSH                            21

/* Side Scan Very High Frequency (higher than the high frequency)         */
#define SUBSYSTEM_SIDESCAN_SSVH                           22

/* Bathymetric Low Frequency (single frequency or the lowest in system)   */
#define SUBSYSTEM_BATHYMETRIC_LF                          40

/* Bathymetric High Frequency (higher than the low frequency)             */
#define SUBSYSTEM_BATHYMETRIC_HF                          41

/* Bathymetric Very High Frequency (higher than the high frequency)       */
#define SUBSYSTEM_BATHYMETRIC_VH                          42

/* Motion Tolerant Side Scan Low Frequency                                */
#define SUBSYSTEM_MT_SIDESCAN_LF                          70

/* Motion Tolerant Side Scan High Frequency                               */
#define SUBSYSTEM_MT_SIDESCAN_HF                          71

/* Motion Tolerant Side Scan Very High Frequency                          */
#define SUBSYSTEM_MT_SIDESCAN_VH                          72


/* ---------------------------------------------------------------------- */
/* Command Message Types                                                  */
/* ---------------------------------------------------------------------- */
/* These messages are sent on the command socket                          */
/* sonarMessage field indicates the type of data to follow.               */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* -------------------------------------------------------------------- */
  /* System level controls - Get only messages                            */
  /* -------------------------------------------------------------------- */

  /* Get the type of system (SonarMessageLongType).  Where:               */
  /*    0 - No Acquisition                                                */
  /*    1 - single frequency multi-pulse sidescan                         */
  /*    4 - simultaneous dual frequency sidescan                          */
  /*    5 - sub-bottom sonar                                              */
  /*    6 - combined sub-bottom and dual frequency sidescan               */
  /*    8 - single frequency sidescan                                     */
  /*    9 - simultaneous dual frequency multi-pulse sidescan              */
  /*   11 - one frequency focused sidescan, one frequency standard        */
  /*   12 - single frequency multipulse Bathymetric system                */
  /*   13 - single frequency single pulse Bathymetric system              */
  /*   14 - single pulse Bathymetric with dual sidescan                   */
  /*   15 - single pulse Bathymetric with dual sidescan & SB              */
  /*   16 - single pulse Bathymetric with triple sidescan & SB            */
  /*   17 - tri-frequency sidescan                                        */
  /*   18 - tri-frequency sidescan & SB                                   */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  /* See SonarMessageSystemTypeReturnType.                                 */
  SONAR_MESSAGE_SYSTEM_TYPE                                =   44,

  /* Get the operational status of the system (SonarMessageLongType).     */
  /* Where:  0 - Operational, 1 - Not operational.                        */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  SONAR_MESSAGE_SYSTEM_OPERATIONAL,

  /* Get the time (TimestampType)                                         */
  /* Note that because of the Nagle algorithm on sockets, the actual      */
  /* message can be delayed.  The Nagle algorithm should be disabled by   */
  /* the sender for more accurate time.                                   */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  SONAR_MESSAGE_SYSTEM_TIME                                =   22,

  /* Discover data logging status (DataLoggingStatusType)                 */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_LOGGING_STATUS                          = 8031,

  /* -------------------------------------------------------------------- */
  /* System level controls - Get and Set messages                         */
  /* -------------------------------------------------------------------- */

  /* Default master subsystem in Discover (SonarMessageLongType)          */
  /* This subsystem will be the master if it is on.  If the master        */
  /* subsystem is not active the bathymetry subsystem if present will be  */
  /* the master, if the bathymetry system is not active, then the lowest  */
  /* active sidescan frequency will be treated as the master.  If no      */
  /* sidescan subsystems are active the sub-bottom if present will be the */
  /* master.                                                              */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_MASTER_SUBSYSTEM                        = 8100,

  /* master subsystem trigger internal (0) (free run), or external (1)    */
  /* (SonarMessageLongType)                                               */
  /* External trigger input in sonar must be configured for external      */
  /* trigger to operate correctly.  Not all sonars have available external*/
  /* triggers.                                                            */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_MASTER_TRIGGER,

  /* Data Logging Commands                                                */
  /* Discover data logging control (DiscoverLoggingControlType)           */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_LOGGING                                 = 8030,

  /* Destination folder for Discover recording (SonarMessageStringType)   */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_LOGGING_DESTINATION                     = 8034,

  /* Enable/disable stave logging: 0=>disable, 1=>enable                  */
  /* (SonarMessageLongType). This command does not affect the logging     */
  /* on/off state. To record stave data, send a 1 with this command and   */
  /* also enable overall logging with DISCOVER_MESSAGE_LOGGING or some    */
  /* other means. If overall logging is off, stave data will not be       */
  /* recorded.                                                            */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  DISCOVER_MESSAGE_LOGGING_RECORD_STAVES                   = 8035,

  /* -------------------------------------------------------------------- */
  /* Sidescan controls - Get and Set messages                             */
  /* -------------------------------------------------------------------- */

  /* Sets the ping rate based on the range in millimeters                 */
  /* (SonarMessageLongType) - use the value 50000 for a 50 meter range.   */
  /* Normally used for sidescan subsystems.                               */
  /* SONAR_MESSAGE_PING_RATE and SONAR_MESSAGE_PING_RANGE are similar in  */
  /* effect and the most recent one received supersedes the other if both */
  /* are sent.                                                            */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  SONAR_MESSAGE_PING_RANGE                                 =  128,

  /* Enable/disable ping: 0 => disable, 1=>enable (SonarMessageLongType)  */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  SONAR_MESSAGE_PING                                       =  120,

  /* 1000.0 * DAC gain to scale outgoing pulse by (SonarMessageLongType)  */
  /* Subsystem and channel must be valid.                                 */
  /* A value of 1000 will apply full power (the maximum amount aka 100%)  */
  /* For sidescan systems values between 0 and 999 are treated as 0.      */
  /* They can be set to either Full power or Off.                         */
  SONAR_MESSAGE_PING_GAIN,

  /* Sets the (multi-ping) operating mode (SonarMessageLongType)          */
  /* Value 0 => Standard operating mode, 1 => Multiple ping mode          */
  /* This is a subsystem command and the channel should be set to 0.      */
  /*                                                                      */
  /* This message is handled by the Discover external topside interface,  */
  /* and switches the mode of the specified                               */
  /* subsystem.                                                           */
  SONAR_MESSAGE_PING_MODE                                  =  131,

  /* -------------------------------------------------------------------- */
  /* Bathymetric controls - Get and Set messages                          */
  /* -------------------------------------------------------------------- */

  /* Topside verification (BathymetricVerificationMessageType)            */
  /*                                                                      */
  /* Topside sends BATHYMETRIC_MESSAGE_TOPSIDE_VERIFICATION set message   */
  /* (COMMAND_SET) with the topsideID value supplied by EdgeTech.         */
  /*                                                                      */
  /* This allows Discover to take topside specific actions if required.   */
  /*                                                                      */
  /* Verification is cleared on command socket disconnection.  Thus it    */
  /* must be performed every time the command socket connects prior to    */
  /* sending commands.                                                    */
  BATHYMETRIC_MESSAGE_TOPSIDE_VERIFICATION                 = 3033,

  /* Bathymetric processing 0 - off, 1 - on (SonarMessageLongType)        */
  /* Note: The system always starts with Bathymetric processing on.       */
  BATHYMETRIC_MESSAGE_PROCESSING                           = 3035,

  /* Binning mode 1 - distance binning, 2 - angle binning                 */
  /* (SonarMessageLongType)                                               */
  BATHYMETRIC_MESSAGE_BIN_MODE,

  /* Distance binning bin size (SonarMessageSingleType)                   */
  /* distance bin size can be from 0.025 meters to 4.0 meters             */
  BATHYMETRIC_MESSAGE_BIN_SIZE,

  /* Angle binning angle size (SonarMessageSingleType)                    */
  /* angle bins can be from 0.25 degrees to 2.0 degrees                   */
  BATHYMETRIC_MESSAGE_ANGLE_WIDTH,

  /* Maximum Swath (SonarMessageSingleType)                               */
  /* maximum swath can be from 10.0 meters to 800.0 meters                */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  BATHYMETRIC_MESSAGE_MAX_SWATH,

  /* Maximum swath gate (BathymetricMaxSwathGateType)                     */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  BATHYMETRIC_MESSAGE_MAX_SWATH_GATE,

  /* -------------------------------------------------------------------- */
  /* Sub-Bottom controls - Get and Set messages                           */
  /* -------------------------------------------------------------------- */

  /* A set message takes no parameters.  A set message resets the list of */
  /* pulse records so that the next get message will return the first     */
  /* record in the list.                                                  */
  /* A get message with a (SonarMessageLongType) parameter, returns up to */
  /* the specified number of pulse records as an array of                 */
  /* (SonarMessagePingEnhancedType) values, up to a maximum of 30.        */
  /* Note that the maximum pulses supported is 30, so requesting 30 will  */
  /* provide all possible pulses in one message.                          */
  /* A get message can also be sent with no parameters, in this case it   */
  /* returns a single (SonarMessagePingEnhancedType) structure.           */
  /* The pulse record following the last valid pulse record will have a   */
  /* NULL pulse name field.                                               */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  SONAR_MESSAGE_PING_LIST_ENHANCED                         =  132,

  /* Select an outgoing set of pulses, and matched filters.               */
  /* (SonarMessageStringType)                                             */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  SONAR_MESSAGE_PING_SELECT                                =  123,

  /* Select an alternate set of outgoing pulses, and matched filters.     */
  /* (SonarMessageStringType)                                             */
  /* When operating in single pulse mode this should be set to NULL.      */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  /* This is currently only supported on multifrequency sub-bottom systems*/
  SONAR_MESSAGE_ALTERNATE_PING_SELECT                      =  134,

  /* Sets the ping rate based on the range in millimeters                 */
  /* (SonarMessageLongType) - use the value 50000 for a 50 meter range.   */
  /* Normally used for sidescan subsystems.                               */
  /* SONAR_MESSAGE_PING_RATE and SONAR_MESSAGE_PING_RANGE are similar in  */
  /* effect and the most recent one received supersedes the other if both */
  /* are sent.                                                            */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
//  SONAR_MESSAGE_PING_RANGE                               =  128,

  /* Number of pings per second required * 1000 (SonarMessageLongType) -  */
  /* use the value 1000 for a 1 Hz rate.                                  */
  /* SONAR_MESSAGE_PING_RATE and SONAR_MESSAGE_PING_RANGE are similar in  */
  /* effect and the most recent one received supersedes the other if both */
  /* are sent.  Only valid for sub-bottom subsystems.                     */
  /* Note:  The subsystem and channel number must be 0.                   */
  SONAR_MESSAGE_PING_RATE                                  =  124,

  /* Enable/disable ping: 0 => disable, 1=>enable (SonarMessageLongType)  */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
//  SONAR_MESSAGE_PING                                     =  120,


  /* Window for sub-bottom data acquisition (DiscoverMessageWindowType)   */
  /* This allows an approximate offset and data window size to be acquired*/
  /* instead of the complete sonar record.  This is most often used to    */
  /* reduce the amount of water column data recorded when using hull      */
  /* mounted sub-bottom profilers in deep water.                          */
  /* Note:  A window size must be specified to use a starting offset.     */
  /* Note:  This is a subsystem command, the channel number must be 0.    */
  DISCOVER_MESSAGE_DATA_WINDOW                            =   8102,

  /* -------------------------------------------------------------------- */
  /* Advanced messages                                                    */
  /* -------------------------------------------------------------------- */

  /* -------------------------------------------------------------------- */
  /* Connectivity verification message                                    */
  /* -------------------------------------------------------------------- */

  /* Alive messages are echoed back on the same connection.  This allows  */
  /* for the detection of lost connection links.  Accepts a long parameter*/
  /* (SonarMessageLongType) which is echoed back to the caller and is     */
  /* typically a sequence number.                                         */
  /* Note:  This is a system command, the subsystem and channel numbers   */
  /* must be 0.                                                           */
  SONAR_MESSAGE_ALIVE                                      =   41,

  /* -------------------------------------------------------------------- */
  /* Data control message                                                 */
  /* -------------------------------------------------------------------- */

  /* Activate / Deactivate return data type.  The data for the subsystem  */
  /* / channel specified in the header is activated / deactivated         */
  /* (0 - deactivate : 1 - activate)   (SonarMessageLongType)             */
  /* Subsystem and channel must be valid.                                 */
  SONAR_MESSAGE_DATA_ACTIVE                                =   83,

}  EdgeTechCommandMessageType;


/* ---------------------------------------------------------------------- */
/* Data Message Types                                                     */
/* ---------------------------------------------------------------------- */
/* These messages are received on the data socket                         */
/* sonarMessage field indicates the type of data to follow.               */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* Status returned (SonarMessageStatusType)                             */
  /* This is returned from the system and is not a command message.       */
  /* Note:  periodic status messages will often be present in the data    */
  SONAR_MESSAGE_SYSTEM_STATUS                              =   40,

  /* Acoustic data returned to topside (JSFDataType)                      */
  /* This is returned from the system and is not a command message.       */
  SONAR_MESSAGE_DATA                                       =   80,

  /* Compressed QC acoustic data returned to topside                      */
  /* (CompactSonarHeaderType)                                             */
  /* This is returned from the sonar and is not a command message.        */
  /* This is rarely used                                                  */
  SONAR_MESSAGE_DATA_COMPACTHEADER                         =   84,

  /* -------------------------------------------------------------------- */
  /* Bathymetric Data Messages                                            */
  /* -------------------------------------------------------------------- */

  /* Bathymetric Data (BathymetricDataMessageType)                        */
  BATHYMETRIC_MESSAGE_DATA                                 = 3000,

  /* Attitude (AttitudeMessageType)                                       */
  BATHYMETRIC_MESSAGE_ATTITUDE,

  /* Pressure (PressureMessageType)                                       */
  BATHYMETRIC_MESSAGE_PRESSURE,

  /* Altitude (AltitudeMessageType)                                       */
  BATHYMETRIC_MESSAGE_ALTITUDE,

  /* Position (PositionMessageType)                                       */
  BATHYMETRIC_MESSAGE_POSITION,

  /* Status (StatusMessageType)                                           */
  BATHYMETRIC_MESSAGE_STATUS,

}  EdgeTechDataMessageType;


/* ---------------------------------------------------------------------- */
/* Message Data Parameters                                                */
/* ---------------------------------------------------------------------- */

/* SONAR_MESSAGE_SYSTEM_OPERATIONAL                                       */
static const int32_t SystemOperationalOperational      = 0;
static const int32_t SystemOperationalNonOperational   = 1;

/* SONAR_MESSAGE_DATA_ACTIVE                                              */
static const int32_t DataActiveDisabled                = 0;
static const int32_t DataActiveEnabled                 = 1;

/* SONAR_MESSAGE_PING                                                     */
static const int32_t PingDisabled                      = 0;
static const int32_t PingEnabled                       = 1;

/* SONAR_MESSAGE_PING_MODE                                                */
static const int32_t PingModeSingle                    = 0;
static const int32_t PingModeMultiple                  = 1;


/* ---------------------------------------------------------------------- */
/* Message Data Structures                                                */
/* ---------------------------------------------------------------------- */
/* The data component of the messages varies with the sonarMessage as     */
/* defined by the structures below.                                       */
/* ---------------------------------------------------------------------- */

/* ---------------------------------------------------------------------- */
/* SONAR_MESSAGE_SYSTEM_TYPE return values                                */
/* ---------------------------------------------------------------------- */
typedef enum
{
  /*    0 - No Acquisition                                                */
  SystemType_No_Acquisition                                            =  0,
  /*    1 - single frequency multi-pulse sidescan                         */
  SystemType_Single_Frequency_Multipulse,
  /*    4 - simultaneous dual frequency sidescan                          */
  SystemType_Dual_Frequency_Sidescan                                   =  4,
  /*    5 - sub-bottom sonar                                              */
  SystemType_Sub_Bottom,
  /*    6 - combined sub-bottom and dual frequency sidescan               */
  SystemType_Sidescan_Sub_Bottom,
  /*    8 - single frequency sidescan                                     */
  SystemType_Single_Frequency_Sidescan                                 =  8,
  /*    9 - simultaneous dual frequency multi-pulse sidescan              */
  SystemType_Dual_Frequency_MultiPulse,
  /*   11 - one frequency focused sidescan, one frequency standard        */
  SystemType_Focused_SideScan                                          = 11,
  /*   12 - single frequency multipulse Bathymetric system                */
  SystemType_Bathymetric_Single_Frequency_Multipulse,
  /*   13 - single frequency single pulse Bathymetric system              */
  SystemType_Bathymetric_Single_Frequency,
  /*   14 - single pulse Bathymetric with dual sidescan                   */
  SystemType_Bathymetric_Dual_Frequency_Sidescan,
  /*   15 - single pulse Bathymetric with dual sidescan & SB              */
  SystemType_Bathymetric_Dual_Frequency_Sidescan_Sub_Bottom,
  /*   16 - single pulse Bathymetric with triple sidescan & SB            */
  SystemType_Bathymetric_Triple_Frequency_Sidescan_Sub_Bottom,
  /*   17 - tri-frequency sidescan                                        */
  SystemType_Triple_Frequency_Sidescan,
  /*   18 - tri-frequency sidescan & SB                                   */
  SystemType_Triple_Frequency_Sidescan_Sub_Bottom,

}  SonarMessageSystemTypeReturnType;


/* ---------------------------------------------------------------------- */
/* Timestamp structure                                                    */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /* Time in seconds since the dawn of time                               */
  /* This is the same value as you get from at time_t - that is time since*/
  /* 1970, only truncated to 32 bits.                                     */
  int32_t time;

  /* Milliseconds supplement to time                                      */
  int32_t milliseconds;

} TimestampType;


/* ---------------------------------------------------------------------- */
/* General integer parameter                                              */
/* ---------------------------------------------------------------------- */

typedef struct
{
  int32_t value;                              /* Value for message          */

}  SonarMessageLongType;


/* ---------------------------------------------------------------------- */
/* General floating point parameter                                       */
/* ---------------------------------------------------------------------- */

typedef struct
{
  float value;                             /* Value for message          */

}  SonarMessageSingleType;


/* ---------------------------------------------------------------------- */
/* General purpose string argument.  - Standard String parameter          */
/* ---------------------------------------------------------------------- */

typedef struct
{
  int8_t name[SONAR_MESSAGE_STRING_LENGTH];

}  SonarMessageStringType;


/* ---------------------------------------------------------------------- */
/* Sonar Runtime alert bit defines.  Referenced in                        */
/* SonarMessageStatusType.runtimeAlerts                                   */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* 0 : Cannot find sonar acquisition device                             */
  SONAR_ALERT_NODEVICE,

  /* 1 : No network connection.                                           */
  SONAR_ALERT_NONETWORK,

  /* 2 : Password expired.                                                */
  SONAR_ALERT_EXPIREDPASSWORD,

  /* 3 : Data recording file error.                                       */
  SONAR_ALERT_RECORDINGFILEERROR,

  /* 4 : Serial port error.                                               */
  SONAR_ALERT_SERIALPORTS,

  /* 5 : Time sync not active, or time error excessive (exceeds 200 ms).  */
  SONAR_ALERT_TIMESYNC,

  /* 6 : System is out of the water, ping rate limits being applied.      */
  SONAR_ALERT_OUTOFWATER,

  /* 7 : One PPS Trigger In Event not active or at wrong rate.            */
  SONAR_ALERT_PPS,

  /* 8 : Container Message received with non-recent time stamp.           */
  SONAR_ALERT_CONTAINERTIMESTAMP,

  /* 9 : Power Amp Fault Detected (e.g. over current or other event).     */
  SONAR_ALERT_DAC_FAULT,

  /*10 : CRC Fault                                                        */
  SONAR_ALERT_IDE_CRCFAULT,

  /*11 : Electronics Hot.  When hot the amp enables will be disabled to   */
  /*     minimize overheating - so not useful data will be received.      */
  SONAR_ALERT_HOT,

  /*12, 13: Preamp sense indicates a wiring error, amp enables will be    */
  /*     disabled to prevent damage - no useful data will be received.    */
  /*     Bit 12 is for SSL preamp sense error, 13 for SSH.                */
  SONAR_ALERT_PREAMPFEEDBACKFAULT_SSL,
  SONAR_ALERT_PREAMPFEEDBACKFAULT_SSH,

  /*14 : No bathymetry calibration file.                                  */
  SONAR_ALERT_NOBATHYCALIBRATION,

  /*15 : Sonar configuration error.                                       */
  SONAR_ALERT_SONAR_CONFIGURATION_ERROR,

  /*16 : No One PPS but UDP / TCP based input device.  See                */
  /* warnIfUdpOrTcpButNoOnePPS in Sonar.txt file.                         */
  SONAR_ALERT_ETHERNET_INPUT_BUT_NO_ONE_PPS,

  /*17 : Serial Port Time In Message Inconsistent With Time Of Receipt    */
  SONAR_ALERT_MESSAGE_TIME_INCONSISTENT_WITH_RECEIPT_TIME,

  /*...: More bits may be added here.                                     */

} SonarAlertEnumType;

/* ---------------------------------------------------------------------- */
/* Defines for reporting of timeStatus field in the SonarMessageStatusType*/
/* record (4 LSBs).                                                       */
/* ---------------------------------------------------------------------- */

typedef enum
{
  TS_SENTENCE_NONE,             /* 0: None                     */
  TS_SENTENCE_CPU,              /* 1: Internal Real Time Clock */
  TS_SENTENCE_NETNOPPS,         /* 2: Network no PPS           */
  TS_SENTENCE_NETPPS,           /* 3: Network with PPS         */
  TS_SENTENCE_ZDA,              /* 4: NMEA ZDA                 */
  TS_SENTENCE_RMC,              /* 5: NMEA RMC                 */
  TS_SENTENCE_GGA,              /* 6: NMEA GGA                 */
  TS_SENTENCE_GLL,              /* 7: NMEA GLL                 */
  TS_SENTENCE_GGK,              /* 8: NMEA GGK                 */
  TS_SENTENCE_TIME__,           /* 9: NMEA like PIXSE,TIME__   */
  TS_SENTENCE_PHINS_BINARY_NAV, /* 10: Phins Binary NAV        */
  TS_SENTENCE_ETC,              /* 11: NMEA like ETC           */
  TS_SENTENCE_POSMV_BINARY,     /* 12: POSMV Binary            */
  /* Note: Values 13-15 Reserved, presently unused.            */
} TimeSyncSentenceType;

typedef enum
{
  /*      0 : Good sync (within 50 ms)                                    */
  TS_STATUS_GOOD = 0,

  /*      1 : Fair sync (within 300 ms)                                   */
  TS_STATUS_FAIR,

  /*      2 : Marginal sync (within 1 second)                             */
  TS_STATUS_MARGINAL,

  /*      3 : Poor sync (1 second or greater)                             */
  TS_STATUS_POOR,

  /*      7 : Failed time sync (no source or large errors)                */
  TS_STATUS_ERROR = 7,

} TimeSyncStatusEnumType;

/* ---------------------------------------------------------------------- */
/* Serial port state codes                                                */
/* ---------------------------------------------------------------------- */

typedef enum
{
  /* 0 : Port is not configured for I/O (inactive).                       */
  SERIAL_PORT_STATE_UNALLOCATED = 0,

  /* 1 : Active and normal operation.                                     */
  SERIAL_PORT_STATE_OK,

  /* 2 : Authorization failure.                                           */
  SERIAL_PORT_STATE_UNAUTHORIZED,

  /* 3 : Port error (e.g. open failed - physical port does not exist)     */
  SERIAL_PORT_STATE_PORT_ERROR,

  /* 4 : Port inactive (no data being received on port)                   */
  SERIAL_PORT_STATE_NO_DATA,

  /* 5 : No valid data - bytes are being received but does not parse.     */
  SERIAL_PORT_NOVALID_DATA,

  /* 6 : Too much data - port idle percent of time is less than the       */
  /*     specified amount (MinIdlePercent keyword value in SonarSerial.ini*/
  /*     file).  Could be caused by too low a baud rate setting.          */
  SERIAL_PORT_STATE_TOOMUCH_DATA,

  /* 7 : Parse errors.                                                    */
  SERIAL_PORT_STATE_PARSE_ERRORS,

  /* 8 : Configuration error.                                             */
  SERIAL_PORT_STATE_CONFIGURATION_ERROR,

  /* 9 : No connection (applies to TCP/UDP based ports).                  */
  SERIAL_PORT_STATE_NO_CONNECTION,

  /* 10: Attempting to open port.                                         */
  SERIAL_PORT_STATE_TRYING_TO_OPEN_PORT,

  /* 11: Open failed - port is in use or does not exist.                  */
  SERIAL_PORT_STATE_OPEN_FAILED,

  /* 12: Port disabled.                                                   */
  SERIAL_PORT_STATE_DISABLED,

  /* 13: Time of receipt differs from time in the message -               */
  /*     (Difference of more than 1 seconds).                             */
  SERIAL_PORT_STATE_TIME_ERRORS,

  /* NOTE: Max value of 15 - must fit in 4 bits.                          */

} SerialPortStateEnumType;

/* ---------------------------------------------------------------------- */
/* SONAR_MESSAGE_STATUS parameters                                        */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /* Incremented each time a ping is dropped, or other internal error     */
  /* events.  One common cause of an incremented overflow count is        */
  /* insufficient network bandwidth (e.g. check link speed/duplex mode).  */
  uint32_t overflowCount;

  /* The current error count.                                             */
  uint32_t errorCount;

  /* Error ids of last 10 errors.                                         */
  int16_t lastError[10];

  /* Disk space available for sonar data storage in kb.                   */
  uint32_t freeDiskSpace;

  /* Indicates that data is being received (increments over time).        */
  uint32_t dataAcquisitionActivityIndicator;

  /* General service warning message                                      */
  /* This is a bit map with one bit for each power on self test status.   */
  /* A non-zero bit indicates a POST test failure.                        */
  /* Bit 0 : SB Power Amp feedback on channel 0 test failed.              */
  /* Bit 1 : SB Power Amp feedback on secondary channel (1) test failed.  */
  /* Bit 2 : Interface Card diagnostic failed.                            */
  /* Bit 3 : Health Monitor Sensors (formerly the 48 Volt Power Check)    */
  /* Bit 4 : Reserved                                                     */
  /* Bit 5 : Internal Configuration Error (Missing Pulse File, etc)       */
  /* Bit 6 : Reserved                                                     */
  /* Bit 7 : Reserved                                                     */
  uint8_t serviceNeeded;

  /* Reserved for future expansion.                                       */
  uint8_t reserved_0[2];

  /* Storage subsystem flags                                              */
  /* Bit 0 : Disk storage is enabled (should be set when on).             */
  /* Bit 1 : Disk primary drive error detected.  Operator needs to reset. */
  /* Bit 2 : Disk write error on drive - all storage disabled.            */
  /* Bit 7 : Disk playback is enabled.                                    */
  uint8_t storageFlags;

  /* Ambient Temperature status.                                          */
  /* 0 : Temperature is OK                                                */
  /* 1 : Temperature is in error - below minimum possible value.          */
  /* 2 : Temperature is below recommended value.                          */
  /* 3 : Temperature is above recommended value.                          */
  /* 4 : Temperature is too high - PINGING IS DISABLED.                   */
  /* 5 : Temperature is in error - above maximum possible value.          */
  uint8_t temperatureStatus;

  /* Status of time synchronization.                                      */
  /* Bits 0-3 : Source for time sync.  See TimeSyncSentenceType above for */
  /*            values.                                                   */
  /* Bits 4-6 : Status of time sync.  See TimeSyncStatusEnumType abvoe.   */
  /*  Bit 7 : If set a PPS is enabled but either not active or not at the */
  /*          expected pulse per second rate.                             */
  uint8_t timeStatus;

  /* Reserved for future expansion.                                       */
  uint16_t reserved_1;

  /* Bottle temperature in Degrees C * 1000.                              */
  int32_t bottleTemperature;

  /* Ambient temperature in Degrees C * 1000.                             */
  int32_t ambientTemperature;

  /* Check of 48 Volt Power in millivolts.                               */
  int32_t power48Volts;

  /* Reserved for future expansion.                                       */
  int32_t reserved_2;

  /* Low rate misc IO analog values.                                      */
  int16_t lowRateIO[4];

  /* Serial Port Summary Status.  There are 4 bits for each of up to 16   */
  /* ports.  Each 4 bit value indicates the state of the port, which can  */
  /* be any of the values listed above in SerialPortStateEnumType         */
  uint8_t serialPortState[8];

  /* Runtime alert bits.  See SonarAlertEnumType for symbolic bit defines */
  int32_t runtimeAlerts;

  /* Reserved for future expansion.                                       */
  int32_t reserved_3[5];

}  SonarMessageStatusType;


/* ---------------------------------------------------------------------- */
/* enhanced ping list entry structure                                     */
/* Ping First / Next data files with enhanced details                     */
/* ---------------------------------------------------------------------- */

/* Maximum pulses per pulse file (for multiping support)                  */

#define MAX_PULSES_PER_PULSEFILE (8)

typedef struct
{
  /* Name used to identify this pulse for selection.                      */
  int8_t fileName[FILE_NAME_SIZE];

  /* Type of pulse.                                                       */
  uint16_t pulseType;

  /* Number of pulses for multiping                                       */
  uint16_t numberOfPulses;

  /* approximate maximum ping rate in Hz.                                 */
  float maxPingRate;

  /* approximate data sample rate in kHz.                                 */
  /* For processed data                                                   */
  float dataRate;

  /* Minimum frequency in Hz.                                             */
  /* Index 0 : Port or single channel                                     */
  /* Index 1 : Starboard if present                                       */
  float fMin[2][MAX_PULSES_PER_PULSEFILE];

  /* Maximum frequency in Hz.                                             */
  /* Index 0 : Port or single channel                                     */
  /* Index 1 : Starboard if present                                       */
  float fMax[2][MAX_PULSES_PER_PULSEFILE];

  /* Pulse duration in milliSeconds                                       */
  float time[2][MAX_PULSES_PER_PULSEFILE];

  /* Unique pulse identifier                                              */
  uint16_t pulseID;

  /* Unused field - round to long boundary.                               */
  uint16_t reserved;

  /* Pulse description - null terminated ASCII string                     */
  int8_t description[SONAR_MESSAGE_STRING_LENGTH];

  /* Type of sonar pulse was designed for.                                */
  uint32_t systemType;

  /* Option bits                                                          */
  /* Bit 0: When set data is basebanded.  When clear data is decimated    */
  /*   This option effects where the data is in the frequency space.      */
  int32_t flags;

  /* The simple conversion from range to rate is:                         */
  /* pingRate = 1 / (rangeMeters / (1500 / 2) + PulseLengthSeconds)       */
  /* This formula is not quite correct and a little more than the         */
  /* pulse length is needed.  The recommended way to compute rate uses the*/
  /* field below, which replaces the PulseLengthSeconds value in above.   */
  float rangeToRateExtraSeconds;

  /* Reserved for future use                                              */
  int32_t reserved2[15];

}  SonarMessagePingEnhancedType;


/* ---------------------------------------------------------------------- */
/* Compact Sonar Data Header Structure                                    */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*  0 -  1 : Ping number (increments with ping)                         */
  uint16_t pingNum;

  /*  2 -  3 : starting Depth (window offset) in samples                  */
  uint16_t startDepth;

  /*  4 -  5 : Maximum absolute value for ADC samples for this packet     */
  uint16_t ADCMax;

  /*  6 -  6 : -- defined as 2 -N volts for LSB                           */
  int8_t weightingFactor;

  /*  7 -  7 : Data format                                                */
  /*   0 = 1 short  per sample  - envelope data                           */
  /*   1 = 2 shorts per sample  - stored as real(1), imaginary(1),        */
  /*   2 = 1 short  per sample  - before matched filter (raw)             */
  /*   3 = 1 short  per sample  - real part analytic signal               */
  /*   NOTE: For type = 1, the total number of bytes of data to follow is */
  /*   4 * samples.  For all other types the total bytes is 2 * samples.  */
  uint8_t dataFormat;

  /*  8 - 11 : Sample interval in ns of stored data                       */
  uint32_t sampleInterval;

  /* 12 - 13 : Millisecond Counter                                        */
  uint16_t millisecondCounter;

  /* 14 - 14 : approximate applied gain = 2 ** (N / 16.0)                 */
  uint8_t appliedGain;

  /* 15 - 15 : Reserved                                                   */
  uint8_t reserved;

  /* Sonar data should follow the header.  The number of samples can be   */
  /* computed from the byteCount in the SonarMessageHeaderType that       */
  /* precedes this header (e.g. for envelope data                         */
  /* samples = (byteCount - sizeof(CompactSonarHeaderType))/2             */
}  CompactSonarHeaderType;


/* ---------------------------------------------------------------------- */
/* DataLoggingStatusStructure - status of recording                       */
/* ---------------------------------------------------------------------- */

typedef struct DataLoggingStatusStructure
{
  /* recording state - current state of recording                         */
  /*               0 - Not recording                                      */
  /*               1 - Recording                                          */
  /*               2 - Error on Recording                                 */
  int32_t                recordingState;

  /* size of recording file in KBytes                                     */
  int32_t                fileSize;

  /* disk free space in MegaBytes                                         */
  int32_t                freeSpace;

  /* name of recording file.                                              */
  SonarMessageStringType  fileName;

  /* reserved for future use                                              */
  int32_t                reserved[16];

}  DataLoggingStatusType;


/* ---------------------------------------------------------------------- */
/* DiscoverLoggingControl - logging command structure                     */
/* ---------------------------------------------------------------------- */

typedef struct DiscoverLoggingControlStructure
{
  /* action - logging action to perform                                   */
  /*      0 - stop logging                                                */
  /*      1 - start logging                                               */
  long int                action;

  /* name of file.  This is the base filename to use for the operation.   */
  /* If absent the current default file name is used.                     */
  SonarMessageStringType  fileName;

}  DiscoverLoggingControlType;


#pragma pack(push, bathyMessages)
#pragma pack(4)

/* ---------------------------------------------------------------------- */
/* Bathymetric verification message structure                             */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Topside ID                                               */
  uint32_t topsideID;

  /*   4 -   7 : Seed/Authorization value                                 */
  uint32_t value;

}  BathymetricVerificationMessageType;


/* ---------------------------------------------------------------------- */
/* Maximum swath gate control message structure                           */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   0 : maximum swath gate active : 0 - inactive, 1 - active     */
  uint8_t    maxSwathGateActive;

  /*   1 -   3 : unused                                                   */
  uint8_t    unused[3];

  /*   4 -   7 : maximum swath gate multiplier              [2.0 -  24.0] */
  float  maximumSwathGate;

}  BathymetricMaxSwathGateType;


/* ---------------------------------------------------------------------- */
/* Bathymetric Message Structures                                         */
/* ---------------------------------------------------------------------- */

#define BATHYMETRIC_DATA_MESSAGE_TYPE_VERSION      (4)

/* ---------------------------------------------------------------------- */
/* Bathymetric Data sample structure                                      */
/* - BathymetricDataMessageType versions 4                                */
/* - bathymetric processor versions 64.0.1.101 - Present                  */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /* time delay of this sample from start time in time scale factor units */
  /* Combine with the time offset to the first sample (timeToFirstSample) */
  /* to get the total time delay.                                         */
  uint16_t timeDelay;

  /* angle in angle scale factor units from nadir of sensor               */
  int16_t angle;

  /* amplitude in 0.5 dB increments                                       */
  uint8_t amplitude;

  /* angle uncertainty in 0.02 degree increments                          */
  uint8_t angleUncertainty;

  /* quality flags                                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit  0: Would be excluded by outlier removal filter                  */
  /* Bit  1: Would be excluded by water column filter                     */
  /* Bit  2: Would be excluded by amplitude filter                        */
  /* Bit  3: Would be excluded by quality filter                          */
  /* Bit  4: Would be excluded by SNR filter                              */
  /* Bit  5: Null content binned data                                     */
  /*         Null content data should not be processed.                   */
  uint8_t qualityFlags;

  /* quality and SNR values defined as follows:                           */
  /* Bits 0 - 4: SNR value in dB 0 - 31+                                  */
  /* Values below 0 are clamped at 0.  Values over 31 are clamped at 31.  */
  /*                                                                      */
  /* Bits 5 - 7: Quality factor:  0 -        quality < 50%                */
  /*                              1 - 50% <= quality < 60%                */
  /*                              2 - 60% <= quality < 70%                */
  /*                              3 - 70% <= quality < 75%                */
  /*                              4 - 75% <= quality < 80%                */
  /*                              5 - 80% <= quality < 85%                */
  /*                              6 - 85% <= quality < 90%                */
  /*                              7 - 90% <= quality                      */
  uint8_t quality;

}  BathymetricSampleType;


/* ---------------------------------------------------------------------- */
/* Bathymetric Data message structure                                     */
/* - BathymetricDataMessageType version 4                                 */
/* - bathymetric processor versions 64.0.1.102 - present                  */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -  11 : Ping Number                                              */
  uint32_t pingNumber;

  /*  12 -  13 : Number of BathymetricSampleType entries after the header */
  uint16_t numberOfSamples;

  /*  14 -  14 : Channel : 0 - port, 1 - starboard                        */
  uint8_t   channel;

  /*  15 -  15 : Algorithm type (0..N)                                    */
  uint8_t   algorithmType;

  /*  16 -  16 : Number of pulses, 1 - single pulse, > 1 - multi-pulse    */
  uint8_t   numberOfPulses;

  /*  17 -  17 : Pulse phase (0 <= x < numberOfPulses)                    */
  uint8_t   pulsePhase;

  /*  18 -  19 : Pulse Length in microseconds                             */
  uint16_t pulseLength;

  /*  20 -  23 : Transmitted pulse amplitude : (0.0 - 1.0)                */
  /* 0 = no power (listen only), 1.0 - maximum power                      */
  float pulseAmplitude;

  /* The center frequency is (startFrequency + endFrequency) / 2 and is   */
  /* different for each multipulse pulse phase.                           */

  /*  24 -  27 : Chirp start frequency (Hz)                               */
  float startFrequency;

  /*  28 -  31 : Chirp end frequency (Hz)                                 */
  float endFrequency;

  /*  32 -  35 : Mixer frequency (Hz)                                     */
  /* The frequency used to mix the acoustic returns to complex (I & Q)    */
  /* basebanded data, normally near the center frequency.                 */
  float mixerFrequency;

  /*  36 -  39 : Sample rate (Hz)                                         */
  /* The A/D Converter output sample rate.  This is Not the sample rate of*/
  /* the bathymetric data set which is determined by the time delays.     */
  float sampleRate;

  /*  40 -  43 : Offset to first sample (nanoseconds)                     */
  uint32_t timeToFirstSample;

  /*  44 -  47 : Time delay uncertainty (seconds)                         */
  /* Maximum time delay error.                                            */
  /* This is the potential acoustic uncertainty of the true delay to each */
  /* detected echo.                                                       */
  /* This time delay uncertainty should be used to to determine the range */
  /* uncertainty for each sample in the packet                            */
  float timeDelayUncertainty;

  /*  48 -  51 : Time scale factor (seconds)                              */
  float timeScaleFactor;

  /*  52 -  55 : Time scale accuracy (percent)                            */
  /* Maximum error in timeDelay value in each BathymetricSampleType entry.*/
  float timeScaleAccuracy;

  /*  56 -  59 : Angle scale factor (degrees)                             */
  float angleScaleFactor;

  /*  60 -  63 : Reserved for future use                                  */
  uint32_t Reserved_01;

  /*  64 -  67 : Offset to first bottom return (nanoseconds)              */
  /* Set to zero if bottom not located.                                   */
  /* This is normally the two way time to the bottom and can be used to   */
  /* derive the sea floor depth in much the same way as a single beam echo*/
  /* sounder.                                                             */
  uint32_t timeToFirstBottomReturn;

  /*  68 -  68 : Version of this message                                  */
  /*             0 - bathymetric processor versions 1.00 - 1.06           */
  /*             1 - bathymetric processor versions 1.07 - 1.13           */
  /*             2 - bathymetric processor versions 1.14 - 63.9.1.102     */
  /*             3 - bathymetric processor versions 63.0.1.103-63.0.1.108 */
  /*               - discover versions 33.0.1.104 - 34.0.1.101            */
  /*             4 - bathymetric processor versions 64.0.1.102 - present  */
  /*               - discover versions 34.0.1.102 - present               */
  /* current version is defined in BATHYMETRIC_DATA_MESSAGE_TYPE_VERSION  */
  uint8_t version;

  /*  69 -  69 : Output Binning                                           */
  /*             0 - all points                                           */
  /*             1 - equi-distance binning                                */
  /*             2 - equi-angle binning                                   */
  uint8_t binning;

  /*  70 -  70 : applied TVG in dB per 100 meters                         */
  uint8_t appliedTVG;

  /*  71 -  71 : Reserved for future use                                  */
  uint8_t reservedA;

  /*  72 -  75 : Span of binned data in this record, in meters or degrees */
  /* depending on the binning type.  The total span is twice this amount  */
  /* If output binning = 0, maximum processing range.                     */
  /* If output binning = 1, # of bins x the bin size. (meters)            */
  /* If output binning = 2, # of beams x the beam width. (degrees)        */
  float totalSpan;

  /*  76 -  79 : Reserved for future use                                  */
  uint32_t reservedB;

  /* -------------------------------------------------------------------- */
  /* Data area begins here                                                */
  /* -------------------------------------------------------------------- */
  /* Data begins at byte 80 having numberOfSamples entries of             */
  /* BathymetricSampleType                                                */
  /*                                                                      */
  /* BathymetricSampleType  data[numberOfSamples];                        */
  /* -------------------------------------------------------------------- */

}  BathymetricDataMessageType;


/* ---------------------------------------------------------------------- */
/* Attitude message structure                                             */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -  11 : Data valid flags:                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit  0: heading                                                      */
  /* Bit  1: heave                                                        */
  /* Bit  2: pitch                                                        */
  /* Bit  3: roll                                                         */
  /* Bit  4: yaw                                                          */
  uint32_t flags;

  /*  12 -  15 : Heading (Degrees) (0.0 - 360.0)                          */
  float heading;

  /*  16 -  19 : Heave (meters)  - down is positive                       */
  float heave;

  /*  20 -  23 : Pitch (degrees) - bow up is positive                     */
  float pitch;

  /*  24 -  27 : Roll (degrees)  - port up is positive                    */
  float roll;

  /*  28 -  31 : Yaw (degrees)  - starboard is positive                   */
  float yaw;

}  AttitudeMessageType;


/* ---------------------------------------------------------------------- */
/* Pressure Message structure                                             */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -  11 : Data valid flags:                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit 0: pressure                                                      */
  /* Bit 1: water temperature                                             */
  /* Bit 2: salt PPM                                                      */
  /* Bit 3: conductivity                                                  */
  /* Bit 4: sound velocity                                                */
  /* Bit 5: depth                                                         */
  uint32_t flags;

  /*  12 -  15 : Absolute Pressure (PSI)                                  */
  float pressure;

  /*  16 -  19 : Water temperature (Degrees C)                            */
  float waterTemperature;

  /*  20 -  23 : Salinity (Parts Per Million)                             */
  float saltPPM;

  /*  24 -  27 : Conductivity (micro-Siemens per cm)                      */
  float conductivity;

  /*  28 -  31 : Velocity of Sound (meters per second)                    */
  float soundVelocity;

  /*  32 -  35 : Depth (meters)                                           */
  float depth;

} PressureMessageType;


/* ---------------------------------------------------------------------- */
/* Altitude Message structure                                             */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -  11 : Data valid flags:                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit 0: altitude                                                      */
  /* Bit 1: speed                                                         */
  /* Bit 2: heading                                                       */
  uint32_t flags;

  /*  12 -  15 : Altitude (meters)                                        */
  float altitude;

  /*  16 -  19 : Speed (Knots)                                            */
  float speed;

  /*  20 -  23 : Heading (Degrees) (0.0 - 360.0)                          */
  float heading;

}  AltitudeMessageType;


/* ---------------------------------------------------------------------- */
/* Position Message structure                                             */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -   9 : Data valid flags:                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit 0: UTM Zone                                                      */
  /* Bit 1: easting                                                       */
  /* Bit 2: northing                                                      */
  /* Bit 3: latitude                                                      */
  /* Bit 4: longitude                                                     */
  /* Bit 5: speed                                                         */
  /* Bit 6: heading                                                       */
  /* Bit 7: altitude                                                      */
  uint16_t flags;

  /*  10 -  11 : UTM Zone                                                 */
  uint16_t UTMZone;

  /*  12 -  19 : Easting (meters)                                         */
  double easting;

  /*  20 -  27 : Northing (meters)                                        */
  double northing;

  /*  28 -  35 : latitude (degrees) north is positive                     */
  double latitude;

  /*  36 -  43 : longitude (degrees) east is positive                     */
  double longitude;

  /*  44 -  47 : Speed (Knots)                                            */
  float speed;

  /*  48 -  51 : Heading (Degrees) (0.0 - 360.0)                          */
  float heading;

  /*  52 -  55 : antennae altitude (meters)                               */
  float altitude;

}  PositionMessageType;


/* ---------------------------------------------------------------------- */
/* Status Message structure                                               */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /*   0 -   3 : Time since 1/1/1970 in seconds (time() value)            */
  uint32_t secondsSince1970;

  /*   4 -   7 : Nanosecond supplement to time                            */
  uint32_t nanoseconds;

  /*   8 -   9 : Data valid flags:                                        */
  /* 0 - clear, 1 - set                                                   */
  /* Bit  0: GGA Status                                                   */
  /* Bit  1: GGK Status                                                   */
  /* Bit  2: Number of Satellites                                         */
  /* Bit  3: Dilution of precision                                        */
  uint16_t flags;

  /*  10 -  10 : Version of this message                                  */
  uint8_t   version;

  /*  11 -  11 : GGA Status                                               */
  uint8_t   GGAStatus;

  /*  12 -  12 : GGK Status                                               */
  uint8_t   GGKStatus;

  /*  13 -  13 : Number of Satellites                                     */
  uint8_t   Satellites;

  /*  14 -  15 : Reserved                                                 */
  uint8_t   ReservedB[2];

  /*  16 -  19 : Dilution of precision                                    */
  float DilutionOfPrecision;

  /*  20 -  63 : Reserved                                                 */
  uint32_t Reserved[11];

}  StatusMessageType;
#pragma pack(pop, bathyMessages)

/* ---------------------------------------------------------------------- */
/* DiscoverMessageWindowType - window sub-bottom data                     */
/* ---------------------------------------------------------------------- */

typedef struct
{
  /* Meters to skip.  The approximate amount of data at the beginning of  */
  /* the record to discard.  This is most often used to eliminate water   */
  /* column data when operated at greater distances from the seafloor.    */
  /* Note: initialSkip value is ignored unless windowSize is non zero.    */
  uint32_t initialSkip;

  /* Meters to keep.  This is the desired amount of data in the record.   */
  /* If zero than all data will be returned (initialSkip is ignored).  If */
  /* non zero than this is the approximate amount of data returned.  If   */
  /* necessary the ping rate will be slowed to accommodate the amount of  */
  /* data requested.                                                      */
  uint32_t windowSize;

}  DiscoverMessageWindowType;

/* ---------------------------------------------------------------------- */
/*                       end InterfaceMessages.h                          */
/* ---------------------------------------------------------------------- */

