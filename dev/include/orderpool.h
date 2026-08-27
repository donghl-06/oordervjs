#pragma once
#include <boost/pool/object_pool.hpp>
#include <memory>
#include <utility>      // std::forward
#include <new>          // placement new
#include "order.h"
#include <queue>

namespace wangcai_orderbook_cpp {

class OrderPool {
public:
    template<typename... Args>
    std::shared_ptr<Order> acquire(Args&&... args)
    {
        // 1. 先 malloc 一块裸内存
        Order* raw = pool_.malloc();

        // 2. placement-new 原地构造
        try {
            new (raw) Order(std::forward<Args>(args)...);
        } catch (...) {                 // 构造失败时回收内存
            pool_.free(raw);
            throw;
        }

        // 3. 用自定义 deleter，注意正确的析构和释放顺序
        return { raw, [this](Order* p){
            if (p) {
                p->~Order();            // 手动调用析构函数
                pool_.free(p);         // 归还内存到池
            }
        }};
    }

private:
    boost::object_pool<Order> pool_ = boost::object_pool<Order>(1024, 0);
};

/*
class OrderPool {
    boost::object_pool<Order> pool_ = boost::object_pool<Order>(1024, 0);
    std::queue<Order*> trash_bin_;
    std::mutex mutex_;
    std::mutex pool_mutex_; // protect pool_ malloc/free

    struct ThreadArg {
        OrderPool* self;
        std::vector<Order*> batch;
    };

    static void* cleanupThread(void* arg) {
    ThreadArg* t = static_cast<ThreadArg*>(arg);
    for (Order* obj : t->batch) {
        obj->~Order();
        std::lock_guard<std::mutex> lock(t->self->pool_mutex_);
        t->self->pool_.free(obj);
    }
    delete t;
    return nullptr;
    }

public:
    template<typename... Args>
    std::shared_ptr<Order> acquire(Args&&... args) {
    Order* raw;
    {
        std::lock_guard<std::mutex> lock(pool_mutex_);
        raw = pool_.malloc();
    }

    try {
        new (raw) Order(std::forward<Args>(args)...);
    } catch (...) {
        std::lock_guard<std::mutex> lock(pool_mutex_);
        pool_.free(raw);
        throw;
    }

    return std::shared_ptr<Order>(raw, [this](Order* p) {
        if (!p) return;

        std::vector<Order*> batch;

        {
            std::lock_guard<std::mutex> lock(mutex_);
            trash_bin_.push(p);

            if (trash_bin_.size() >= 1000) {
                while (!trash_bin_.empty()) {
                    batch.push_back(trash_bin_.front());
                    trash_bin_.pop();
                }
            }
        }

        if (!batch.empty()) {
            ThreadArg* arg = new ThreadArg{ this, std::move(batch) };
            pthread_t tid;
            pthread_create(&tid, nullptr, &OrderPool::cleanupThread, arg);
            pthread_detach(tid);
        }
    });
    }

};
*/
} // namespace wangcai_orderbook_cpp