const express=require('express');
const http=require('http');
const {Server}=require('socket.io');
const grpc=require('@grpc/grpc-js');
const protoLoader=require('@grpc/proto-loader');
const path=require('path');
const app=express(); app.use(express.json({limit:'1mb'}));
const server=http.createServer(app);
const io=new Server(server,{cors:{origin:process.env.FRONTEND_ORIGIN||'http://127.0.0.1:5173'}});
const PORT=Number(process.env.PORT||3000); const BRAIN_URL=process.env.PYTHON_BRAIN_URL||'http://127.0.0.1:8000'; const GRPC_ADDRESS=process.env.GRPC_ADDRESS||'127.0.0.1:50051';
let client=null;
try {const def=protoLoader.loadSync(path.resolve(__dirname,'../../proto/telemetry.proto'),{keepCase:true,longs:String,enums:String,defaults:true,oneofs:true});const proto=grpc.loadPackageDefinition(def).trakivo.superbase;client=new proto.TelemetryService(GRPC_ADDRESS,grpc.credentials.createInsecure());} catch(e){console.error('[gateway] protobuf setup failed:',e.message);}
app.get('/health',(_req,res)=>res.json({status:'ok',service:'trakivo-node-gateway'}));
const { normalizeFrame } = require('./telemetry-utils');

app.get('/api/analyze',async(req,res)=>{const start=Number(req.query.start??0),end=Number(req.query.end??start+10);if(!Number.isFinite(start)||!Number.isFinite(end)||start<0||end<start)return res.status(400).json({error:'Provide valid non-negative distances; end must be >= start.'});if(!client)return res.status(503).json({error:'Telemetry gRPC client unavailable. Check protobuf configuration.'});client.GetTelemetrySlice({start_distance:start,end_distance:end},async(err,response)=>{if(err)return res.status(503).json({error:`Telemetry engine unavailable: ${err.message}`});try{const r=await fetch(`${BRAIN_URL}/analyze`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({frames:(response?.frames||[]).map(normalizeFrame)}),signal:AbortSignal.timeout(15000)});const body=await r.json().catch(()=>({}));if(!r.ok)return res.status(502).json({error:body.detail||body.error||`Python brain returned ${r.status}`});return res.json(body);}catch(e){return res.status(502).json({error:`Python AI service unavailable: ${e.message}`});}});});
io.on('connection',socket=>{let call=null;const stop=()=>{if(call)call.cancel();call=null;};socket.on('subscribe_telemetry',data=>{stop();if(!client){socket.emit('telemetry_error','Telemetry gRPC client unavailable.');return;}const start=Number(data?.start??0);if(!Number.isFinite(start)||start<0){socket.emit('telemetry_error','Invalid start distance.');return;}call=client.StreamLiveTelemetry({start_distance:start,end_distance:0});call.on('data',f=>socket.emit('telemetry_update',normalizeFrame(f)));call.on('error',e=>{if(e.code!==grpc.status.CANCELLED)socket.emit('telemetry_error',`Telemetry stream error: ${e.message}`);});call.on('end',()=>{call=null;});});socket.on('unsubscribe_telemetry',stop);socket.on('disconnect',stop);});
if(require.main===module)server.listen(PORT,'127.0.0.1',()=>console.log(`[TRAKIVO] Gateway listening at http://127.0.0.1:${PORT}`));
module.exports={app,server,normalizeFrame};
