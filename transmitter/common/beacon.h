#ifndef BEACON_H
#define BEACON_H

#include <stdint.h>

/**
 * @brief Beacon packet structure for RF tracking modules
 * Fixed 6-byte packet format transmitted by all tracking modules.
 */

typedef struct {
    uint32_t device_id;      
    uint16_t sequence_num;   
} BeaconPacket;

#endif