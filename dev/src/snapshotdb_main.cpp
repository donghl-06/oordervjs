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

        int s = 0;
        std::string str;
        char op;
        while(true){
            std::cout << "查询快照, t为时间查找, i为id查找, c为变化id查找, q为退出: ";
            std::cin >> op;
            if(op == 't'){
                std::cout << "查询快照, (09:25:00 - 15:00:00): ";
                std::cin >> str;
                str = date + " " + str;
                //std::cout << str << std::endl;
                s = engine.snapshot_db_.get_id_by_timestamp(str);
                //std::cout << engine.snapshot_db_.get_timestamp_by_id(s) << std::endl;
            }else if (op == 'i'){
                std::cout << "查询快照, (1 - " << engine.snapshot_db_.size() - 1 << "): ";
                std::cin >> s;
            }else if (op == 'c'){
                std::cout << "查询快照, (1 - " << engine.snapshot_db_.change_cnt - 1 << "): ";
                int a;
                std::cin >> a;
                s = engine.snapshot_db_.get_id_by_changeindex(a);
            }else if (op == 'd'){
                s++;
            }else if (op == 'a'){
                s--;
            }else if (op == 'x'){
                int a = engine.snapshot_db_.get_changeindex_by_id(s);
                s = engine.snapshot_db_.get_id_by_changeindex(a + 1);
            }else if (op == 'z'){
                int a = engine.snapshot_db_.get_changeindex_by_id(s);
                s = engine.snapshot_db_.get_id_by_changeindex(a - 1);
            }else if (op == 'q'){
                break;
            }else continue;
            
            auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>> ();
            auto metadata = engine.snapshot_db_.get_metadata(s);
            std::cout << "快照时间: " << engine.snapshot_db_.get_timestamp_by_id(s) << std::endl;
            std::cout << "快照变化索引: " << engine.snapshot_db_.get_changeindex_by_id(s) << std::endl;
            std::cout << "快照id: " << s << std::endl;
            for(int i = SnapshotDB::metadata::recorded_bid_ask_num - 1; i >= 0; i--)
                std::cout << "卖" << std::to_string(i + 1) << ": " << metadata.best_asks_snapshots[i] << std::endl;
            for(int i = 0; i < SnapshotDB::metadata::recorded_bid_ask_num; i++)
                std::cout << "买" << std::to_string(i + 1) << ": " << metadata.best_bids_snapshots[i] << std::endl;

            std::cout<< "买一挂单量: " << metadata.best_bid_create_count            << std::endl
                     << "买一撤单量: " << metadata.best_bid_cancel_count            << std::endl
                     << "买一成交量: " << metadata.best_bid_traded_count            << std::endl
                     << "卖一挂单量: " << metadata.best_ask_create_count            << std::endl
                     << "卖一撤单量: " << metadata.best_ask_cancel_count            << std::endl
                     << "卖一成交量: " << metadata.best_ask_traded_count            << std::endl
                     ;
            engine.snapshot_db_.query(s, result, engine.getExchange());
            for (auto& [price, vec] : *result) {
                std::string tmp_order_id = "";
                for(auto &i : vec){
                    if(i.order_local_id == tmp_order_id){
                        std::cout << "warning: repeated storage in (" << i.order_local_id << ")" << i.remaining_volume() << " $" << i.price << std::endl;
                    }
                    tmp_order_id = i.order_local_id;
                }
            }

            for(int i = SnapshotDB::metadata::recorded_bid_ask_num - 1; i >= 0; i--){
                uint64_t sum = 0;
                uint64_t price = metadata.best_asks_snapshots[i];
                std::cout << "卖" << std::to_string(i + 1) << ": " << (*result)[price].size() << "个数据: ";
                for(int j = 0; j != (*result)[price].size(); j++){
                    std::cout 
                        //<< "(" << (*result)[price][j].order_local_id << ")" 
                        //<< (*result)[price][j].remaining_volume() << " "
                    ;
                    sum += (*result)[price][j].remaining_volume();
                }
                std::cout << "共计: " << sum << std::endl;
            }
            for(int i = 0; i < SnapshotDB::metadata::recorded_bid_ask_num; i++){
                uint64_t sum = 0;
                uint64_t price = metadata.best_bids_snapshots[i];
                std::cout << "买" << std::to_string(i + 1) << ": " << (*result)[price].size() << "个数据: ";
                for(int j = 0; j != (*result)[price].size(); j++){
                    std::cout 
                        //<< "(" << (*result)[price][j].order_local_id << ")" 
                        //<< (*result)[price][j].remaining_volume() << " "
                    ;
                    sum += (*result)[price][j].remaining_volume();
                }
                std::cout << "共计: " << sum << std::endl;
            }

            
            // for(auto o : *list){
            //     std::cout << o.order_id        << " "
            //         << o.order_local_id << " "
            //         << o.account << " "
            //         << o.price << " "
            //         << o.volume << " "
            //         << o.traded_volume  << " "
            //         << o.timestamp  << " "
            //         << "\n";
            // }
            // std::cout << "找到了" << list->size() << "个结果， 最后5项:\n";
            // for(int i = list->size() - 5; i < list->size(); i++){
            //     std::cout << (*list)[i].order_id        << " "
            //         << (*list)[i].order_local_id << " "
            //         << (*list)[i].account << " "
            //         << (*list)[i].price << " "
            //         << (*list)[i].volume << " "
            //         << (*list)[i].traded_volume  << " "
            //         << (*list)[i].timestamp  << " "
            //         << "\n";
            // }
        }
        
    } catch (const std::exception& e) {
        std::cerr << "回测失败: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
} 
