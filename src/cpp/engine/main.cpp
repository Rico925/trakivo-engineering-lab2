#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>
#include <grpcpp/grpcpp.h>
#include "telemetry.grpc.pb.h"
using grpc::Server; using grpc::ServerBuilder; using grpc::ServerContext; using grpc::Status;
using trakivo::superbase::TelemetryFrame; using trakivo::superbase::TelemetryRequest; using trakivo::superbase::TelemetryService; using trakivo::superbase::TelemetryStreamResponse;
class TelemetryBuffer { public: void Push(const TelemetryFrame& f){std::lock_guard<std::mutex> l(m_); frames_.push_back(f); if(frames_.size()>100000)frames_.erase(frames_.begin(),frames_.begin()+10000);} std::vector<TelemetryFrame> Slice(double a,double b){std::lock_guard<std::mutex> l(m_);std::vector<TelemetryFrame> out;for(const auto& f:frames_)if(f.race_distance()>=a&&f.race_distance()<=b)out.push_back(f);return out;} private:std::mutex m_;std::vector<TelemetryFrame> frames_;};
TelemetryBuffer buffer; std::atomic<bool> running{true};
TelemetryFrame MakeFrame(double d){TelemetryFrame f;f.set_race_distance(d);f.set_video_timestamp_ms(static_cast<std::uint64_t>(d*1000));f.set_speed_kmh(285+10*std::sin(d/25));f.set_rpm(11000+500*std::sin(d/10));f.set_throttle_pct(75+20*std::sin(d/15));f.set_brake_pct((d>30&&d<35)?35:0);f.set_steering_angle(2*std::sin(d/8));(*f.mutable_sensors())["tire_fl_temp"]=90+15*std::sin(d/18);(*f.mutable_sensors())["oil_pressure"]=3.2;if(std::fmod(d,97.0)<0.01){f.set_is_anomaly(true);f.set_anomaly_type("DemoSensorSpike");}return f;}
void Worker(){double d=0;while(running.load()){buffer.Push(MakeFrame(d));d+=0.1;std::this_thread::sleep_for(std::chrono::milliseconds(100));}}
class ServiceImpl final:public TelemetryService::Service{Status GetTelemetrySlice(ServerContext*,const TelemetryRequest* r,TelemetryStreamResponse* out)override{if(r->end_distance()<r->start_distance())return Status(grpc::StatusCode::INVALID_ARGUMENT,"end_distance must be >= start_distance");for(const auto& f:buffer.Slice(r->start_distance(),r->end_distance()))*out->add_frames()=f;return Status::OK;} Status StreamLiveTelemetry(ServerContext* c,const TelemetryRequest* r,grpc::ServerWriter<TelemetryFrame>* w)override{double cursor=r->start_distance();while(!c->IsCancelled()&&running.load()){auto batch=buffer.Slice(cursor,cursor+2);for(const auto& f:batch){if(f.race_distance()<cursor)continue;if(!w->Write(f))return Status::OK;cursor=f.race_distance()+0.1;}std::this_thread::sleep_for(std::chrono::milliseconds(100));}return Status::OK;}};
int main(){const std::string address="127.0.0.1:50051";ServiceImpl service;ServerBuilder b;b.AddListeningPort(address,grpc::InsecureServerCredentials());b.RegisterService(&service);std::unique_ptr<Server> server(b.BuildAndStart());if(!server){std::cerr<<"Failed to start gRPC server on "<<address<<std::endl;return 1;}std::cout<<"[TRAKIVO] C++ telemetry engine listening on "<<address<<std::endl;std::thread worker(Worker);server->Wait();running=false;worker.join();return 0;}
