'use strict';
function normalizeFrame(f){const sensors={};for(const [k,v] of Object.entries(f.sensors||{}))sensors[k]=Number(v);return {race_distance:Number(f.race_distance||0),video_timestamp_ms:String(f.video_timestamp_ms||'0'),speed_kmh:Number(f.speed_kmh||0),rpm:Number(f.rpm||0),throttle_pct:Number(f.throttle_pct||0),brake_pct:Number(f.brake_pct||0),steering_angle:Number(f.steering_angle||0),sensors,is_anomaly:Boolean(f.is_anomaly),anomaly_type:String(f.anomaly_type||'')};}
module.exports = { normalizeFrame };
