// src/python_bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>

#include "backtest_engine.hpp"
#include "orderdb.hpp"

namespace py = pybind11;
using namespace wangcai_orderbook_cpp;
using namespace pybind11::literals;  // 启用 "_a" 语法

PYBIND11_MODULE(pywangcai_orderbook, m) {
    m.doc() = "WangCai Trading System - 交易系统可视化查询工具";

    // ========== 快照元数据类 ==========
    py::class_<SnapshotDB::metadata>(m, "SnapshotMetadata")
        .def_readwrite("best_bids_snapshots", &SnapshotDB::metadata::best_bids_snapshots)
        .def_readwrite("best_asks_snapshots", &SnapshotDB::metadata::best_asks_snapshots)
        .def_readwrite("best_bid_create_count", &SnapshotDB::metadata::best_bid_create_count)
        .def_readwrite("best_bid_cancel_count", &SnapshotDB::metadata::best_bid_cancel_count)
        .def_readwrite("best_bid_traded_count", &SnapshotDB::metadata::best_bid_traded_count)
        .def_readwrite("best_ask_create_count", &SnapshotDB::metadata::best_ask_create_count)
        .def_readwrite("best_ask_cancel_count", &SnapshotDB::metadata::best_ask_cancel_count)
        .def_readwrite("best_ask_traded_count", &SnapshotDB::metadata::best_ask_traded_count);

    // ========== 交易可视化引擎主类 ==========
    py::class_<BacktestEngine>(m, "TradingVisualizer")
        .def(py::init<const std::string&, const std::string&, const std::string&>(),
             py::arg("symbol"), py::arg("date"), py::arg("data_path"),
             "创建交易可视化引擎")
        
        .def("run", &BacktestEngine::run, "运行数据处理")
        
        // 带进度回调的运行方法
        .def("run_with_progress", [](BacktestEngine& self, py::function progress_callback) {
            // 设置进度回调
            self.setProgressCallback([progress_callback](double progress, const std::string& message) {
                // 在Python中调用回调函数
                try {
                    progress_callback(progress, message);
                } catch (const py::error_already_set& e) {
                    // 忽略Python回调中的异常，避免影响C++处理
                    // 简单地忽略异常，不调用discard_as_unraisable
                }
            });
            
            // 运行处理
            self.run();
        }, py::arg("progress_callback"), "运行数据处理并返回进度信息")
        
        // 获取基础信息
        .def("get_total_snapshots", [](BacktestEngine& self) {
            return self.snapshot_db_.size();
        }, "获取总快照数量")
        
        .def("get_total_changes", [](BacktestEngine& self) {
            return self.snapshot_db_.change_cnt;
        }, "获取总变化数量")

        // 仅获取市场数据（不包含详细订单信息）
        .def("query_market_data", [](BacktestEngine& self, const std::string& date, const std::string& time_str) {
            std::string full_timestamp = date + " " + time_str;
            uint64_t snapshot_id = self.snapshot_db_.get_id_by_timestamp(full_timestamp);
            
            if (snapshot_id == 0) {
                return py::dict();
            }
            
            auto metadata = self.snapshot_db_.get_metadata(snapshot_id);
            
            py::dict response;
            response["snapshot_id"] = snapshot_id;
            response["timestamp"] = self.snapshot_db_.get_timestamp_by_id(snapshot_id);
            response["change_index"] = self.snapshot_db_.get_changeindex_by_id(snapshot_id);
            
            // 仅包含市场数据
            py::dict market_data;
            market_data["best_bids"] = metadata.best_bids_snapshots;
            market_data["best_asks"] = metadata.best_asks_snapshots;
            market_data["bid_create_count"] = metadata.best_bid_create_count;
            market_data["bid_cancel_count"] = metadata.best_bid_cancel_count;
            market_data["bid_traded_count"] = metadata.best_bid_traded_count;
            market_data["ask_create_count"] = metadata.best_ask_create_count;
            market_data["ask_cancel_count"] = metadata.best_ask_cancel_count;
            market_data["ask_traded_count"] = metadata.best_ask_traded_count;
            response["market_data"] = market_data;
            
            return response;
        }, py::arg("date"), py::arg("time_str"), "仅获取市场数据（不包含详细订单信息）")
        
        // 按时间查询快照
        .def("query_by_time", [](BacktestEngine& self, const std::string& date, const std::string& time_str) {
            std::string full_timestamp = date + " " + time_str;
            uint64_t snapshot_id = self.snapshot_db_.get_id_by_timestamp(full_timestamp);
            
            if (snapshot_id == 0) {
                return py::dict();
            }
            
            auto metadata = self.snapshot_db_.get_metadata(snapshot_id);
            auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>>();
            self.snapshot_db_.query(snapshot_id, result, self.getExchange());
            
            py::dict response;
            response["snapshot_id"] = snapshot_id;
            response["timestamp"] = self.snapshot_db_.get_timestamp_by_id(snapshot_id);
            response["change_index"] = self.snapshot_db_.get_changeindex_by_id(snapshot_id);
            
            
            py::dict market_data;
            market_data["best_bids"] = metadata.best_bids_snapshots;
            market_data["best_asks"] = metadata.best_asks_snapshots;
            market_data["bid_create_count"] = metadata.best_bid_create_count;
            market_data["bid_cancel_count"] = metadata.best_bid_cancel_count;
            market_data["bid_traded_count"] = metadata.best_bid_traded_count;
            market_data["ask_create_count"] = metadata.best_ask_create_count;
            market_data["ask_cancel_count"] = metadata.best_ask_cancel_count;
            market_data["ask_traded_count"] = metadata.best_ask_traded_count;
            response["market_data"] = market_data;
            
            // 各档位详细订单信息
            py::dict levels;
            std::vector<std::pair<std::string, uint64_t>> level_names;
            for(int i = 0; i < metadata.best_bids_snapshots.size(); i++)
                level_names.push_back({"bid" + std::to_string(i + 1), metadata.best_bids_snapshots[i]});
            for(int i = 0; i < metadata.best_asks_snapshots.size(); i++)
                level_names.push_back({"ask" + std::to_string(i + 1), metadata.best_asks_snapshots[i]});
            
            for (const auto& [level_name, price] : level_names) {
                py::list orders_info;
                uint64_t total_volume = 0;
                
                if (result->find(price) != result->end()) {
                    auto& orders = (*result)[price];
                    std::sort(orders.begin(), orders.end(), 
                             [](const Order& a, const Order& b) {
                                 return a.order_id < b.order_id;
                             });
                    
                    for (const auto& order : orders) {
                        py::dict order_info;
                        order_info["order_local_id"] = order.order_local_id;
                        order_info["remaining_volume"] = order.remaining_volume();
                        order_info["order_id"] = order.order_id;
                        order_info["direction"] = (order.direction == Direction::Buy) ? "Buy" : "Sell";
                        orders_info.append(order_info);
                        total_volume += order.remaining_volume();
                    }
                }
                
                py::dict level_data;
                level_data["price"] = price;
                level_data["order_count"] = orders_info.size();
                level_data["total_volume"] = total_volume;
                level_data["orders"] = orders_info;
                levels[level_name.c_str()] = level_data;
            }
            
            response["levels"] = levels;
            return response;
            
        }, py::arg("date"), py::arg("time_str"), "按时间查询快照")
        
        // 按快照ID查询
        .def("query_by_id", [](BacktestEngine& self, uint64_t snapshot_id) {
            if (snapshot_id > self.snapshot_db_.size()) {
                return py::dict();
            }
            
            auto metadata = self.snapshot_db_.get_metadata(snapshot_id);
            auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>>();
            self.snapshot_db_.query(snapshot_id, result, self.getExchange());
            
            py::dict response;
            response["snapshot_id"] = snapshot_id;
            response["timestamp"] = self.snapshot_db_.get_timestamp_by_id(snapshot_id);
            response["change_index"] = self.snapshot_db_.get_changeindex_by_id(snapshot_id);
            
            
            py::dict market_data;
            market_data["best_bids"] = metadata.best_bids_snapshots;
            market_data["best_asks"] = metadata.best_asks_snapshots;
            market_data["bid_create_count"] = metadata.best_bid_create_count;
            market_data["bid_cancel_count"] = metadata.best_bid_cancel_count;
            market_data["bid_traded_count"] = metadata.best_bid_traded_count;
            market_data["ask_create_count"] = metadata.best_ask_create_count;
            market_data["ask_cancel_count"] = metadata.best_ask_cancel_count;
            market_data["ask_traded_count"] = metadata.best_ask_traded_count;
            response["market_data"] = market_data;
            
            // 各档位详细订单信息
            py::dict levels;
            std::vector<std::pair<std::string, uint64_t>> level_names;
            for(int i = 0; i < metadata.best_bids_snapshots.size(); i++)
                level_names.push_back({"bid" + std::to_string(i + 1), metadata.best_bids_snapshots[i]});
            for(int i = 0; i < metadata.best_asks_snapshots.size(); i++)
                level_names.push_back({"ask" + std::to_string(i + 1), metadata.best_asks_snapshots[i]});
            
            for (const auto& [level_name, price] : level_names) {
                py::list orders_info;
                uint64_t total_volume = 0;
                
                if (result->find(price) != result->end()) {
                    auto& orders = (*result)[price];
                    std::sort(orders.begin(), orders.end(), 
                             [](const Order& a, const Order& b) {
                                 return a.order_id < b.order_id;
                             });
                    
                    for (const auto& order : orders) {
                        py::dict order_info;
                        order_info["order_local_id"] = order.order_local_id;
                        order_info["remaining_volume"] = order.remaining_volume();
                        order_info["order_id"] = order.order_id;
                        order_info["direction"] = (order.direction == Direction::Buy) ? "Buy" : "Sell";
                        orders_info.append(order_info);
                        total_volume += order.remaining_volume();
                    }
                }
                
                py::dict level_data;
                level_data["price"] = price;
                level_data["order_count"] = orders_info.size();
                level_data["total_volume"] = total_volume;
                level_data["orders"] = orders_info;
                levels[level_name.c_str()] = level_data;
            }
            
            response["levels"] = levels;
            return response;
            
        }, py::arg("snapshot_id"), "按快照ID查询")
        
        // 按变化索引查询
        .def("query_by_change_index", [](BacktestEngine& self, uint64_t change_index) {
            uint64_t snapshot_id = self.snapshot_db_.get_id_by_changeindex(change_index);
            if (snapshot_id == 0) {
                return py::dict();
            }
            
            // 复制按ID查询的逻辑
            auto metadata = self.snapshot_db_.get_metadata(snapshot_id);
            auto result = std::make_shared<std::map<uint64_t, std::vector<Order>>>();
            self.snapshot_db_.query(snapshot_id, result, self.getExchange());
            
            py::dict response;
            response["snapshot_id"] = snapshot_id;
            response["timestamp"] = self.snapshot_db_.get_timestamp_by_id(snapshot_id);
            response["change_index"] = self.snapshot_db_.get_changeindex_by_id(snapshot_id);
            
            
            py::dict market_data;
            market_data["best_bids"] = metadata.best_bids_snapshots;
            market_data["best_asks"] = metadata.best_asks_snapshots;
            market_data["bid_create_count"] = metadata.best_bid_create_count;
            market_data["bid_cancel_count"] = metadata.best_bid_cancel_count;
            market_data["bid_traded_count"] = metadata.best_bid_traded_count;
            market_data["ask_create_count"] = metadata.best_ask_create_count;
            market_data["ask_cancel_count"] = metadata.best_ask_cancel_count;
            market_data["ask_traded_count"] = metadata.best_ask_traded_count;
            response["market_data"] = market_data;
            
            py::dict levels;
            std::vector<std::pair<std::string, uint64_t>> level_names;
            for(int i = 0; i < metadata.best_bids_snapshots.size(); i++)
                level_names.push_back({"bid" + std::to_string(i + 1), metadata.best_bids_snapshots[i]});
            for(int i = 0; i < metadata.best_asks_snapshots.size(); i++)
                level_names.push_back({"ask" + std::to_string(i + 1), metadata.best_asks_snapshots[i]});
            
            for (const auto& [level_name, price] : level_names) {
                py::list orders_info;
                uint64_t total_volume = 0;
                
                if (result->find(price) != result->end()) {
                    auto& orders = (*result)[price];
                    std::sort(orders.begin(), orders.end(), 
                             [](const Order& a, const Order& b) {
                                 return a.order_id < b.order_id;
                             });
                    
                    for (const auto& order : orders) {
                        py::dict order_info;
                        order_info["order_local_id"] = order.order_local_id;
                        order_info["remaining_volume"] = order.remaining_volume();
                        order_info["order_id"] = order.order_id;
                        order_info["direction"] = (order.direction == Direction::Buy) ? "Buy" : "Sell";
                        orders_info.append(order_info);
                        total_volume += order.remaining_volume();
                    }
                }
                
                py::dict level_data;
                level_data["price"] = price;
                level_data["order_count"] = orders_info.size(); 
                level_data["total_volume"] = total_volume;
                level_data["orders"] = orders_info;
                levels[level_name.c_str()] = level_data;
            }
            
            response["levels"] = levels;
            return response;
            
        }, py::arg("change_index"), "按变化索引查询")
        
        // 获取时间范围信息
        .def("get_time_range", [](BacktestEngine& self) {
            py::dict time_info;
            if (self.snapshot_db_.size() > 0) {
                time_info["start_time"] = self.snapshot_db_.get_timestamp_by_id(1);
                time_info["end_time"] = self.snapshot_db_.get_timestamp_by_id(self.snapshot_db_.size());
            }
            return time_info;
        }, "获取时间范围信息");

    // ========== 便捷函数 ==========
    m.def("create_visualizer", [](const std::string& symbol, const std::string& date, const std::string& data_path) {
        return std::make_unique<BacktestEngine>(symbol, date, data_path);
    }, py::arg("symbol"), py::arg("date"), py::arg("data_path"),
      "创建交易可视化器的便捷函数");
    
    m.def("format_price", [](uint64_t price) {
        return price / 10000.0;
    }, py::arg("price"), "将内部价格格式转换为元单位");
}