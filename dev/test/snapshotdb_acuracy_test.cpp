#include "../include/orderdb.hpp"
#include "orderbook.h"
#include "call_auction_engine.hpp"
#include "con_auction_engine.hpp"
#include "close_auction_engine.hpp"
#include "OrderLoader.h"
#include "backtest_engine.hpp"
#include <queue>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace wangcai_orderbook_cpp;

struct checkdata{
    std::vector<uint64_t> bids  ;
    std::vector<uint64_t> asks  ;
    std::vector<uint64_t> bsizes;
    std::vector<uint64_t> asizes;
    checkdata(){}
    checkdata(std::vector<uint64_t> &bids_  ,
              std::vector<uint64_t> &asks_  ,
              std::vector<uint64_t> &bsizes_,
              std::vector<uint64_t> &asizes_)
              {
                for(auto &i : bids_  )bids  .push_back(i);
                for(auto &i : asks_  )asks  .push_back(i);
                for(auto &i : bsizes_)bsizes.push_back(i);
                for(auto &i : asizes_)asizes.push_back(i);
              }
    bool operator==(const checkdata& cd_)const{
        if(bids  .size() != cd_.bids  .size())return false;
        if(asks  .size() != cd_.asks  .size())return false;
        if(bsizes.size() != cd_.bsizes.size())return false;
        if(asizes.size() != cd_.asizes.size())return false;
        for(int i = 0; i < bids  .size(); i++)if(bids  [i] != cd_.bids  [i])return false;
        for(int i = 0; i < asks  .size(); i++)if(asks  [i] != cd_.asks  [i])return false;
        for(int i = 0; i < bsizes.size(); i++)if(bsizes[i] != cd_.bsizes[i])return false;
        for(int i = 0; i < asizes.size(); i++)if(asizes[i] != cd_.asizes[i])return false;
        return true;
    }
    void show(){
        std::cout << "bids   :"; for(int i = 0; i < bids  .size(); i++)std::cout << bids  [i] << " ";
        std::cout << "asks   :"; for(int i = 0; i < asks  .size(); i++)std::cout << asks  [i] << " ";
        std::cout << "bsizes :"; for(int i = 0; i < bsizes.size(); i++)std::cout << bsizes[i] << " ";
        std::cout << "asizes :"; for(int i = 0; i < asizes.size(); i++)std::cout << asizes[i] << " ";
        std::cout << std::endl;
    }
};
long long parse_scaled(const std::string &tmp, int scale = 10000) {
    // scale = 10000 代表保留 4 位小数
    size_t dot = tmp.find('.');
    std::string int_part, frac_part;

    if (dot == std::string::npos) {
        int_part = tmp;
        frac_part = "";
    } else {
        int_part = tmp.substr(0, dot);
        frac_part = tmp.substr(dot + 1);
    }

    // 去掉小数部分多余的位数或补零
    while (frac_part.size() < 4) frac_part.push_back('0');
    if (frac_part.size() > 4) frac_part = frac_part.substr(0, 4);

    return std::stoll(int_part) * scale + std::stoll(frac_part);
}
std::map<std::string, checkdata> load_bids_asks_from_csv(const std::string& csv_file, int num_record) {

    std::map<std::string, checkdata> result;
    std::ifstream file(csv_file);
    std::string line;
    std::getline(file, line); // 跳过CSV文件的标题行
    

    while (std::getline(file, line)) {
        if (!line.empty()) {
                try {
                std::istringstream ss(line);
                std::string datetime, tmp;
                std::vector<uint64_t> bids  ;
                std::vector<uint64_t> asks  ;
                std::vector<uint64_t> bsizes;
                std::vector<uint64_t> asizes;
                
                std::getline(ss, datetime, ',');// datetime    
                for(int i = 0; i < 9; i++)std::getline(ss, tmp, ',');// sym prevclose open high low close volume turnover tradecount
                
                for(int i = 0; i < 10; i++){
                    std::getline(ss, tmp, ',');
                    if(i < num_record)bids  .push_back(parse_scaled(tmp));
                    std::getline(ss, tmp, ',');
                    if(i < num_record)bsizes.push_back(std::stoi(tmp));
                }

                for(int i = 0; i < 10; i++){
                    std::getline(ss, tmp, ',');
                    if(i < num_record)asks  .push_back(parse_scaled(tmp));
                    std::getline(ss, tmp, ',');
                    if(i < num_record)asizes.push_back(std::stoi(tmp));
                }
                result.emplace(datetime, checkdata(bids, asks, bsizes, asizes));
            } catch (const std::exception& e) {
                std::cerr << "处理价格数据时发生错误: " << e.what() << std::endl;
            }
        }
    }
    return result;
}

const int NUM_RECORDED = std::min(uint(10), SnapshotDB::metadata::recorded_bid_ask_num); // max SnapshotDB::metadata::recorded_bid_ask_num

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cout << "用法: backtest_main <symbol> <date> <data_path>" << std::endl;
        return 1;
    }
    
    std::string symbol = argv[1];
    std::string date = argv[2];
    std::string data_path = argv[3];
    
    try {
        // 创建回测引擎
        BacktestEngine engine(symbol, date, data_path);
        
        // 启用交易记录功能，输出到指定文件
        std::string trade_output_file = data_path + "/SnapshotDB_main" + symbol + "_" + date + ".csv";
        //engine.enableTradeRecording(trade_output_file);
        
        // 设置市场数据回调（可选，用于调试）
        engine.setMarketDataCallback([](const MarketData& data) {
            // if (data.event_type == "trade") {
            //     std::cout << "[市场数据] " << data.datetime << " 成交: " 
            //              << data.last_price / 10000.0 << " 数量: " << data.last_volume << std::endl;
            // }
        });
        
        // 创建并注册策略
        // auto strategy1 = std::make_shared<MeanReversionStrategy>("均值回归策略1", 0.01);
        // auto strategy2 = std::make_shared<MeanReversionStrategy>("均值回归策略2", 0.02);
        
        // engine.registerStrategy(strategy1);
        // engine.registerStrategy(strategy2);
        
        // 运行回测
        engine.run();
        
        // 输出结果
        auto positions = engine.getPositions();
        double total_pnl = engine.getTotalPnL();
        
        std::cout << "\n最终盈亏: " << total_pnl << " 元" << std::endl;
        
        // 交易记录统计信息
        const auto& trades = engine.getTradeRecords();
        std::cout << "回测期间总成交笔数: " << trades.size() << std::endl;
        if (!trades.empty()) {
            std::cout << "首笔成交时间: " << trades.front().datetime << std::endl;
            std::cout << "末笔成交时间: " << trades.back().datetime << std::endl;
        }

        // 查询速度测试
        // clock_t begin = clock();
        // for(int i = 0; i < 1000; i++){
        //     auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>> ();
        //     engine.snapshot_db_.query(i * 1000, result);
        // }
        // clock_t end = clock();
        // std::cout << "Time for 1000 query: " << end - begin << std::endl;

        std::string cstick_file = data_path + "/cstick_" + symbol + "_" + date + ".csv";
        //std::cout << cstick_file << std::endl;
        auto cstick = load_bids_asks_from_csv(cstick_file, NUM_RECORDED);
        //std::cout << cstick.size() << std::endl;

        int cnt = 0;
        for(auto i = cstick.lower_bound(date + " 09:26:00"); i != cstick.end() && i->first < (date + " 14:57:00"); i++){
            checkdata cd_;
            std::vector<checkdata> cd_vec;
            bool match = 0;
            int s = engine.snapshot_db_.get_id_by_timestamp(i->first);
            cnt++;
            while(true){
                //i->second.show();
                //std::cout <<i->first << " " <<  engine.snapshot_db_.get_timestamp_by_id(s).substr(0, 19) << std::endl;
                if(i->first < engine.snapshot_db_.get_timestamp_by_id(s).substr(0, 19))break;
                auto metadata = engine.snapshot_db_.get_metadata(s);

                auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>> ();
                engine.snapshot_db_.query(s, result);
                
                std::vector<uint64_t> bsizes;
                std::vector<uint64_t> asizes;
                for(int j = 0; j < NUM_RECORDED; j++){
                    uint64_t sum = 0;
                    uint64_t price = metadata.best_asks_snapshots[j];
                    for(int k = 0; k != (*result)[price].size(); k++){
                        sum += (*result)[price][k].remaining_volume();
                    }
                    asizes.push_back(sum);
                }
                for(int j = 0; j < NUM_RECORDED; j++){
                    uint64_t sum = 0;
                    uint64_t price = metadata.best_bids_snapshots[j];
                    for(int k = 0; k != (*result)[price].size(); k++){
                        sum += (*result)[price][k].remaining_volume();
                    }
                    bsizes.push_back(sum);
                }
                
                std::vector<uint64_t> bids;
                std::vector<uint64_t> asks;
                for(int j = 0; j < NUM_RECORDED; j++)
                    bids.push_back(metadata.best_bids_snapshots[j]);
                for(int j = 0; j < NUM_RECORDED; j++)
                    asks.push_back(metadata.best_asks_snapshots[j]);

                cd_ = checkdata(bids,
                    asks,
                    bsizes,
                    asizes
                );
                cd_vec.push_back(cd_);

                //cd_.show();

                if (cd_ == i->second){
                    match = 1;
                    //std::cout <<i->first << " matched with changeid ";
                    //std::cout << engine.snapshot_db_.get_changeindex_by_id(s) << "" << " id " << s << std::endl;
                    //cd_.show();
                    //i->second.show();
                    break;
                }

                //s++;
                int a = engine.snapshot_db_.get_changeindex_by_id(s);
                s = engine.snapshot_db_.get_id_by_changeindex(a + 1);
            }
            if(match){
                if(cnt%1000 == 0){
                    std::cout << i->first << " and previous 1000 timestamps matched!\n"; 
                }
                
            }
            else {
                std::cout << i->first << " does not match!\n"; 
                std::cout << "expected:\n";
                i->second.show();
                std::cout << "get:\n";
                for(auto &cd : cd_vec)cd.show();
            }

        }

        
        
    } catch (const std::exception& e) {
        std::cerr << "回测失败: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
} 
