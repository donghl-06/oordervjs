#ifndef ORDER_DB_HPP
#define ORDER_DB_HPP
#include <iostream>
#include <iomanip>
#include <cmath>
#include <vector>
#include <map>
#include "../include/order.h"
#include <algorithm>
#include <fstream>

namespace wangcai_orderbook_cpp {
const int DEGREE = 10;
const int MIN_KEYS = (DEGREE + 1) / 2 - 1;
// Forward declare
struct Node;
using NodePtr = std::shared_ptr<Node>;

struct Node {
    bool leaf;
    virtual void query(std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result) const = 0;
    virtual NodePtr clone() const = 0;
    virtual ~Node() = default;
};

// ---- Leaf Node ----
struct LeafNode : public Node {
    std::vector<uint64_t> keys;
    std::vector<std::shared_ptr<Order>> orders;

    LeafNode() { leaf = true; }

    NodePtr clone() const override {
        auto n = std::make_shared<LeafNode>();
        n->keys = keys;
        n->orders = orders;
        return std::static_pointer_cast<Node>(n);
    }

    void query(std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result) const override {
        for (const auto& order : orders) {
            result->operator[](order->price).push_back(*order);
        }
    }
};

// ---- Internal Node ----
struct InternalNode : public Node {
    std::vector<uint64_t> keys;
    std::vector<NodePtr> children;

    InternalNode() { leaf = false; }

    NodePtr clone() const override {
        auto n = std::make_shared<InternalNode>();
        n->keys = keys;
        n->children = children;
        return std::static_pointer_cast<Node>(n);
    }

    void query(std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result) const override{
        int cnt = 0;
        for(auto i : children)
            i->query(result);
    }
};



class BPlusTree {
    NodePtr root;

public:
    BPlusTree() {
        root = std::make_shared<LeafNode>();
    }

    BPlusTree(NodePtr r) : root(r) {}

    BPlusTree insert(const Order& order) const;

    BPlusTree remove(uint64_t order_id) const;

    BPlusTree modify(uint64_t order_id, const Order& order) const;

    void traverse(std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result) const;

    NodePtr getRoot() const;
    
private:
    

    // Returns true if split happens
    bool insertInternal(NodePtr node, const Order& order, NodePtr& newChild, uint64_t& newKey) const;

    NodePtr removeInternal(NodePtr node, uint64_t key, bool& shrink) const;

    NodePtr modifyInternal(NodePtr node, uint64_t key, const Order& order) const;

    bool tryBorrowOrMerge(std::shared_ptr<InternalNode> parent, int idx, NodePtr left, NodePtr right) const;
};

class SnapshotDB {
public:
    //快照元数据变化计数
    uint64_t change_cnt;
    struct metadata{
        //元数据记录到买几卖几
        static const uint recorded_bid_ask_num = 3;

        std::array<uint64_t, recorded_bid_ask_num> best_bids_snapshots;// 买一, 买二, 买三
        std::array<uint64_t, recorded_bid_ask_num> best_asks_snapshots;// 卖一, 卖二, 卖三
        uint64_t best_bid_create_count;// 买一累计挂单量
        uint64_t best_bid_cancel_count;// 买一累计撤单量
        uint64_t best_bid_traded_count;// 买一累计成交量
        uint64_t best_ask_create_count;// 卖一累计挂单量
        uint64_t best_ask_cancel_count;// 卖一累计撤单量
        uint64_t best_ask_traded_count;// 卖一累计成交量
        metadata(
            std::array<uint64_t, recorded_bid_ask_num> best_bids_snapshots_   = {},
            std::array<uint64_t, recorded_bid_ask_num> best_asks_snapshots_   = {},
            uint64_t                                 best_bid_create_count_ = 0,
            uint64_t                                 best_bid_cancel_count_ = 0,
            uint64_t                                 best_bid_traded_count_ = 0,
            uint64_t                                 best_ask_create_count_ = 0,
            uint64_t                                 best_ask_cancel_count_ = 0,
            uint64_t                                 best_ask_traded_count_ = 0
        ):  best_bids_snapshots  (best_bids_snapshots_  ), 
            best_asks_snapshots  (best_asks_snapshots_  ), 
            best_bid_create_count(best_bid_create_count_),
            best_bid_cancel_count(best_bid_cancel_count_),
            best_bid_traded_count(best_bid_traded_count_),
            best_ask_create_count(best_ask_create_count_),
            best_ask_cancel_count(best_ask_cancel_count_),
            best_ask_traded_count(best_ask_traded_count_){}
    };
    
    SnapshotDB():change_cnt(0){
        metadata_snapshots[0] = metadata();
        add_changeindex();
        add_timestamp("");
    }

    ~SnapshotDB();

    //在最新快照上插入并新建快照
    void insert(const Order& order);

    //在最新快照上移除并新建快照
    void remove(uint64_t order_id);

    //在最新快照上修改并新建快照
    void modify(uint64_t order_id, const Order& order);

    //按照id查询
    void query(const uint64_t& id, std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result, std::string exchange = "SZ");

    //获取时间戳前的最新id 时间戳格式"xxxx-xx-xx xx:xx:xx.xxx"
    uint64_t get_id_by_timestamp(const std::string& timestamp_);

    //从元数据变化计数索引获取id
    uint64_t get_id_by_changeindex(const uint64_t& change_index_);

    //获取id前最新的时间戳
    std::string get_timestamp_by_id(const uint64_t& id);

    //获取id前最新的变化计数索引
    uint64_t get_changeindex_by_id(const uint64_t& id);

    //插入变化计数 (不新建快照)
    void add_changeindex();

    //插入时间戳 (不新建快照)
    void add_timestamp(std::string timestamp_);

    uint64_t size(){return snapshots.size();}

    //从id获取元数据
    metadata get_metadata(uint64_t id) const {
        auto it = metadata_snapshots.upper_bound(id);
        if (it == metadata_snapshots.begin()) return metadata(); // 没有 <= id 的记录
        --it;
        return it->second;
    }

    //将元数据记录绑定到最新快照id
    void insert_metadata(metadata metadata_);

    
private:
    const BPlusTree& getLatest() const;

    std::vector<BPlusTree>          snapshots         ;//id to snapshot
    std::map<uint64_t, uint64_t>    changeindexs_to_id;// change_index -> id
    std::map<std::string, uint64_t> timestamps_to_id  ;// timestamp -> id
    
    std::map<uint64_t, uint64_t>    id_to_changeindex;// id -> change_index (reverse map)
    std::map<uint64_t, std::string> id_to_timestamp  ;// id -> timestamp (reverse map)

    std::map<uint64_t, metadata> metadata_snapshots;

};

}
#endif