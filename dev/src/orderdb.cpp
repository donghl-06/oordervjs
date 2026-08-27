#include "../include/orderdb.hpp"

#include <iostream>
#include <iomanip>
#include <cmath>
#include <vector>
#include <map>
#include <algorithm>
#include <queue>
#include <stack>
using namespace wangcai_orderbook_cpp;

// optional

//递归销毁, 栈高可达95层
//SnapshotDB::~SnapshotDB(){}

//迭代销毁, 避免爆栈, 栈高最高18层, 析构时间增加100%, 内存占用最大增加200MB
SnapshotDB::~SnapshotDB(){
    std::stack<NodePtr> nodes;

    for(auto &snapshot : snapshots){
        auto root = snapshot.getRoot();
        if(!root) return;
        nodes.push(root);
        root.reset();
    }
        
    while(!nodes.empty()) {
        NodePtr current = nodes.top();
        nodes.pop();

        if(!current)continue;

        if(!current->leaf) {
            auto internal = std::static_pointer_cast<InternalNode>(current);

            for(NodePtr &child : internal->children) {
                if(child)nodes.push(child);
            }

            internal->children.clear();
        }
    }
}

// 插入一个订单，返回插入后的新B+树（不可变结构，原树不变）
BPlusTree BPlusTree::insert(const Order& order) const {
    auto newRoot = root->clone(); // 克隆当前根节点，保证不可变
    NodePtr out_new_child;
    uint64_t out_new_key = 0;
    // 递归插入，out_new_child和out_new_key用于分裂时返回新节点和分裂键
    bool split = insertInternal(newRoot, order, out_new_child, out_new_key);
    if (split) {
        // 如果根节点分裂，创建新的根节点
        auto newRootNode = std::make_shared<InternalNode>();
        newRootNode->keys.push_back(out_new_key);
        newRootNode->children.push_back(newRoot);
        newRootNode->children.push_back(out_new_child);
        return BPlusTree(std::static_pointer_cast<Node>(newRootNode));
    }
    return BPlusTree(newRoot);
}

// 删除指定order_id的订单，返回删除后的新B+树
BPlusTree BPlusTree::remove(uint64_t order_id) const {
    auto cloned = root->clone(); // 克隆根节点
    bool shrink = false;
    NodePtr newChild = removeInternal(cloned, order_id, shrink);

    // 如果根节点只有一个子节点且是InternalNode，则降一层
    if (auto internal = std::dynamic_pointer_cast<InternalNode>(newChild);
        internal && internal->children.size() == 1) {
        return BPlusTree(internal->children[0]);
    }
    
    return BPlusTree(newChild);
}

// 修改指定order_id的订单，返回删除后的新B+树
BPlusTree BPlusTree::modify(uint64_t order_id, const Order& order) const {
    auto cloned = root->clone(); // 克隆根节点
    NodePtr newChild = modifyInternal(cloned, order_id, order);
    
    return BPlusTree(newChild);
}

// 遍历整棵树，将所有订单按order_id聚合到result中
void BPlusTree::traverse(std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result) const {
    root->query(result);  
}

// 获取根节点
NodePtr BPlusTree::getRoot() const { return root; }

// 递归插入内部实现，处理分裂逻辑
bool BPlusTree::insertInternal(NodePtr node, const Order& order,
                    NodePtr& newChild, uint64_t& newKey) const {
    if (node->leaf) {
        // 叶子节点插入
        auto leaf = std::static_pointer_cast<LeafNode>(node);
        auto it = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), order.order_id);
        size_t idx = it - leaf->keys.begin();

        leaf->keys.insert(it, order.order_id);
        leaf->orders.insert(leaf->orders.begin() + idx, std::make_shared<Order>(order));

        if (leaf->keys.size() > DEGREE) {
            // 叶子节点分裂
            auto newLeaf = std::make_shared<LeafNode>();
            size_t mid = leaf->keys.size() / 2;

            // 分裂后右半部分给新叶子
            newLeaf->keys.assign(leaf->keys.begin() + mid, leaf->keys.end());
            newLeaf->orders.assign(leaf->orders.begin() + mid, leaf->orders.end());

            // 原叶子只保留左半部分
            leaf->keys.erase(leaf->keys.begin() + mid, leaf->keys.end());
            leaf->orders.erase(leaf->orders.begin() + mid, leaf->orders.end());


            newKey = newLeaf->keys.front(); // 新分裂键
            newChild = std::static_pointer_cast<Node>(newLeaf);
            return true;
        }

        return false;
    } else {
        // 内部节点插入
        auto internal = std::dynamic_pointer_cast<InternalNode>(node);
        // upper_bound找到第一个大于order_id的位置
        int idx = std::upper_bound(internal->keys.begin(), internal->keys.end(), order.order_id) - internal->keys.begin();
        
        NodePtr child = internal->children[idx]->clone(); // 克隆子节点
        internal->children[idx] = child;
        
        NodePtr newNode;
        uint64_t midKey;
        bool split = insertInternal(child, order, newNode, midKey);
        
        if (!split) return false;
        
        // 子节点分裂后，插入新键和新子节点
        internal->keys.insert(internal->keys.begin() + idx, midKey);
        internal->children.insert(internal->children.begin() + idx + 1, newNode);

        if (internal->keys.size() > DEGREE) {
            // 内部节点分裂
            int mid = DEGREE / 2;
            auto newInternal = std::make_shared<InternalNode>();
            
            newKey = internal->keys[mid]; // 分裂键
            
            // 新内部节点获得右半部分
            newInternal->keys.assign(internal->keys.begin() + mid + 1, internal->keys.end());
            newInternal->children.assign(internal->children.begin() + mid + 1, internal->children.end());
            
            // 原内部节点只保留左半部分
            internal->keys.erase(internal->keys.begin() + mid, internal->keys.end());
            internal->children.erase(internal->children.begin() + mid + 1, internal->children.end());

            
            newChild = newInternal;
            return true;
        }

        return false;
    }
}

// 递归删除内部实现，处理合并/借用逻辑
NodePtr BPlusTree::removeInternal(NodePtr node, uint64_t key, bool& shrink) const {
    if (node->leaf) {
        // 叶子节点删除
        auto leaf = std::dynamic_pointer_cast<LeafNode>(node);
        int idx = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key) - leaf->keys.begin();
        if (idx >= leaf->keys.size() || leaf->keys[idx] != key){
            std::cout << "not found\n";
            return node;  // 未找到
        }
        leaf->keys.erase(leaf->keys.begin() + idx);
        leaf->orders.erase(leaf->orders.begin() + idx);

        shrink = (leaf->keys.size() < MIN_KEYS); // 判断是否需要合并
        return leaf;
    }

    // 内部节点删除
    auto internal = std::dynamic_pointer_cast<InternalNode>(node);
    int idx = std::upper_bound(internal->keys.begin(), internal->keys.end(), key) - internal->keys.begin();

    NodePtr child = internal->children[idx]->clone();
    bool childShrink = false;
    NodePtr newChild = removeInternal(child, key, childShrink);

    internal->children[idx] = newChild;

    // optional
    // 如果子节点缩小，尝试合并或借用
    // 合并后树的高度更低，查询加快20%，建库时间减慢100%
    // if (childShrink) {
    //     NodePtr left = idx > 0 ? internal->children[idx - 1]->clone() : nullptr;
    //     NodePtr right = idx + 1 < internal->children.size() ? internal->children[idx + 1]->clone() : nullptr;
    // 
    //     if(left)internal->children[idx - 1] = left;
    //     if(right)internal->children[idx + 1] = right;
    // 
    //     if (tryBorrowOrMerge(internal, idx, left, right)) {
    //         shrink = (internal->keys.size() < MIN_KEYS);
    //     }
    // }

    return std::static_pointer_cast<Node>(internal);
}

// 尝试从兄弟节点借用或合并节点，返回是否发生了合并
bool BPlusTree::tryBorrowOrMerge(std::shared_ptr<InternalNode> parent, int idx,
                          NodePtr left, NodePtr right) const {
    auto child = parent->children[idx];

    if(child->leaf){
    // 尝试从左兄弟借用
    if (left && left->leaf) {
        auto l = std::dynamic_pointer_cast<LeafNode>(left);
        auto c = std::dynamic_pointer_cast<LeafNode>(child);

        if (l->keys.size() > MIN_KEYS) {
            // 从左兄弟借最后一个元素
            c->keys.insert(c->keys.begin(), l->keys.back());
            c->orders.insert(c->orders.begin(), l->orders.back());
            l->keys.pop_back();
            l->orders.pop_back();
            parent->keys[idx - 1] = c->keys.front(); // 更新父节点分隔键
            return false;
        }
    }

    // 尝试从右兄弟借用
    if (right && right->leaf) {
        auto r = std::dynamic_pointer_cast<LeafNode>(right);
        auto c = std::dynamic_pointer_cast<LeafNode>(child);

        if (r->keys.size() > MIN_KEYS) {
            // 从右兄弟借第一个元素
            c->keys.push_back(r->keys.front());
            c->orders.push_back(r->orders.front());
            r->keys.erase(r->keys.begin());
            r->orders.erase(r->orders.begin());
            parent->keys[idx] = r->keys.front(); // 更新父节点分隔键
            return false;
        }
    }

    // 与左兄弟合并
    if (left && left->leaf) {
        auto l = std::dynamic_pointer_cast<LeafNode>(left);
        auto c = std::dynamic_pointer_cast<LeafNode>(child);
        l->keys.insert(l->keys.end(), c->keys.begin(), c->keys.end());
        l->orders.insert(l->orders.end(), c->orders.begin(), c->orders.end());
        //l->next = c->next; // 可选：维护链表
        parent->children.erase(parent->children.begin() + idx);
        parent->keys.erase(parent->keys.begin() + idx - 1);
        return true;
    }

    // 与右兄弟合并
    if (right && right->leaf) {
        auto r = std::dynamic_pointer_cast<LeafNode>(right);
        auto c = std::dynamic_pointer_cast<LeafNode>(child);
        c->keys.insert(c->keys.end(), r->keys.begin(), r->keys.end());
        c->orders.insert(c->orders.end(), r->orders.begin(), r->orders.end());
        //c->next = r->next; // 可选：维护链表
        parent->children.erase(parent->children.begin() + idx + 1);
        parent->keys.erase(parent->keys.begin() + idx);
        return true;
    }
    }
    else{
        auto c = std::dynamic_pointer_cast<InternalNode>(child);

        // 从左兄弟借用
        if (left && !left->leaf) {
            auto l = std::dynamic_pointer_cast<InternalNode>(left);
            if (l->keys.size() > MIN_KEYS) {
                // 借用逻辑
                c->keys.insert(c->keys.begin(), parent->keys[idx-1]);
                c->children.insert(c->children.begin(), l->children.back());
                parent->keys[idx-1] = l->keys.back();
                l->keys.pop_back();
                l->children.pop_back();
                return false;
            }
        }

        // 从右兄弟借用
        if (right && !right->leaf) {
            auto r = std::dynamic_pointer_cast<InternalNode>(right);
            if (r->keys.size() > MIN_KEYS) {
                // 借用逻辑
                c->keys.push_back(parent->keys[idx]);
                c->children.push_back(r->children.front());
                parent->keys[idx] = r->keys.front();
                r->keys.erase(r->keys.begin());
                r->children.erase(r->children.begin());
                return false;
            }
        }

        // 与左兄弟合并
        if (left && !left->leaf) {
            auto l = std::dynamic_pointer_cast<InternalNode>(left);
            // 关键修复：将父节点分隔键下移
            l->keys.push_back(parent->keys[idx-1]);
            l->keys.insert(l->keys.end(), c->keys.begin(), c->keys.end());
            l->children.insert(l->children.end(), c->children.begin(), c->children.end());
            parent->children.erase(parent->children.begin() + idx);
            parent->keys.erase(parent->keys.begin() + idx - 1);
            return true;
        }

        // 与右兄弟合并
        if (right && !right->leaf) {
            auto r = std::dynamic_pointer_cast<InternalNode>(right);
            // 关键修复：将父节点分隔键下移
            c->keys.push_back(parent->keys[idx]);
            c->keys.insert(c->keys.end(), r->keys.begin(), r->keys.end());
            c->children.insert(c->children.end(), r->children.begin(), r->children.end());
            parent->children.erase(parent->children.begin() + idx + 1);
            parent->keys.erase(parent->keys.begin() + idx);
            return true;
        }
    }
    return false;
}

// 递归修改内部实现
NodePtr BPlusTree::modifyInternal(NodePtr node, uint64_t key, const Order& order) const{
    if (node->leaf) {
        // 叶子节点修改
        auto leaf = std::dynamic_pointer_cast<LeafNode>(node);
        int idx = std::lower_bound(leaf->keys.begin(), leaf->keys.end(), key) - leaf->keys.begin();
        if (idx >= leaf->keys.size() || leaf->keys[idx] != key){
            std::cout << "not found\n";
            return node;  // 未找到
        }
        //leaf->keys.erase(leaf->keys.begin() + idx);
        //leaf->orders.erase(leaf->orders.begin() + idx);
        leaf->orders[idx] = std::make_shared<Order>(order);

        return leaf;
    }

    // 内部节点修改
    auto internal = std::dynamic_pointer_cast<InternalNode>(node);
    int idx = std::upper_bound(internal->keys.begin(), internal->keys.end(), key) - internal->keys.begin();

    NodePtr child = internal->children[idx]->clone();
    NodePtr newChild = modifyInternal(child, key, order);

    internal->children[idx] = newChild;
    return internal;
}





// SnapshotDB相关实现

// 插入订单到最新快照，生成新快照
void SnapshotDB::insert(const Order& order) {
    auto newTree = getLatest().insert(order);
    snapshots.push_back(newTree);
}

// 从最新快照中删除订单，生成新快照
void SnapshotDB::remove(uint64_t order_id) {
    auto newTree = getLatest().remove(order_id);
    snapshots.push_back(newTree);
}

// 从最新快照中修改订单，生成新快照
void SnapshotDB::modify(uint64_t order_id, const Order& order){
    auto newTree = getLatest().modify(order_id, order);
    snapshots.push_back(newTree);
}

// 查询指定id的快照，将所有订单聚合到result
void SnapshotDB::query(const uint64_t& id, std::shared_ptr<std::map<uint64_t, std::vector<Order>>> result, std::string exchange) {
    if(id < 0 || id >= snapshots.size()){
        std::cout << "Snapshot " << id << " not found.\n";
        return;
    }
    snapshots[id].traverse(result);
    if(exchange == "SZ"){
        //std::cout << "sorting by local id" << std::endl;
        for (auto& [price, vec] : *result) 
            std::sort(vec.begin(), vec.end(), [](const Order& a, const Order& b) {
                return a.order_local_id < b.order_local_id;
            });
    }
    else if (exchange == "SH"){
        //std::cout << "sorting by bizindex" << std::endl;
        for (auto& [price, vec] : *result) 
            std::sort(vec.begin(), vec.end(), [](const Order& a, const Order& b) {
                return a.bizindex < b.bizindex;
            });
    }
}

// 获取最新的B+树快照
const BPlusTree& SnapshotDB::getLatest() const {
    if (snapshots.empty()) {
        static BPlusTree empty;
        return empty;
    }
    return *snapshots.rbegin();
}

// 添加时间戳与快照id的映射
void SnapshotDB::add_timestamp(std::string timestamp_) {
    if(id_to_timestamp.find(size() - 1) != id_to_timestamp.end())return;
    timestamps_to_id[timestamp_] = size() - 1;
    id_to_timestamp[size() - 1] = timestamp_;
}

// 添加变更序号与快照id的映射
void SnapshotDB::add_changeindex() {
    if(id_to_changeindex.find(size() - 1) != id_to_changeindex.end())return;
    changeindexs_to_id[change_cnt] = size() - 1;
    id_to_changeindex[size() - 1] = change_cnt;
    ++change_cnt;
}

// 根据时间戳查找对应快照id（小于等于该时间戳的最大id）
uint64_t SnapshotDB::get_id_by_timestamp(const std::string& timestamp_) {
    auto it = timestamps_to_id.upper_bound(timestamp_); // 找到第一个 > timestamp_ 的 entry
    if (it == timestamps_to_id.begin()) {
        return 0;
    }
    --it; // 回退一个，即为 <= timestamp_ 的最大 key
    return it->second;
}

// 根据变更序号查找对应快照id（小于等于该变更序号的最大id）
uint64_t SnapshotDB::get_id_by_changeindex(const uint64_t& change_index_) {
    auto it = changeindexs_to_id.upper_bound(change_index_); // 找到第一个 > change_index_ 的 entry
    if (it == changeindexs_to_id.begin()) {
        return 0;
    }
    --it; // 回退一个，即为 <= change_index_ 的最大 key
    return it->second;
}

// 根据快照id查找对应时间戳（小于等于该id的最大时间戳）
std::string SnapshotDB::get_timestamp_by_id(const uint64_t& id) {
    auto it = id_to_timestamp.upper_bound(id); // 找到第一个 > id 的 entry
    if (it == id_to_timestamp.begin()) {
        return "";
    }
    --it; // 回退一个，即为 <= id 的最大 key
    return it->second;
}

// 根据快照id查找对应变更序号（小于等于该id的最大变更序号）
uint64_t SnapshotDB::get_changeindex_by_id(const uint64_t& id) {
    auto it = id_to_changeindex.upper_bound(id); // 找到第一个 > id 的 entry
    if (it == id_to_changeindex.begin()) {
        return 0;
    }
    --it; // 回退一个，即为 <= id 的最大 key
    return it->second;
}

// 插入元数据到当前快照
void SnapshotDB::insert_metadata(metadata metadata_){
    metadata_snapshots[size() - 1] = metadata_;
}
