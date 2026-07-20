# SQL Agent 测评报告
| 指标 | 数值 |
|------|------|
| 测试用例数 | 10 |
| 成功率 | 100.0% |
| 平均重试次数 | 0.0 |

## 测试结果：

### 1. 哪个产品卖得最多？ — ✅ (重试 0次)
```sql
SELECT p.name AS 产品名称, SUM(o.quantity) AS 总销量
FROM orders o
JOIN products p ON o.product_id = p.id
GROUP BY p.id, p.name
ORDER BY 总销量 DESC
LIMIT 1
```
**解释**: 这条SQL查询是在找出所有产品中，哪个产品的总销量最高，并返回它的名称和总销量。

### 2. 北京的用户花了多少钱？ — ✅ (重试 0次)
```sql
SELECT u.name AS 用户名, SUM(o.total_amount) AS 总花费
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.city = '北京'
GROUP BY u.id, u.name;
```
**解释**: 这个查询是在找出所有住在北京的用户，然后把每个用户的所有订单金额加起来，算出每个人一共花了多少钱。

### 3. 各城市的订单总额排名 — ✅ (重试 0次)
```sql
SELECT u.city AS 城市, SUM(o.total_amount) AS 订单总额
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.city
ORDER BY 订单总额 DESC
```
**解释**: 这句话是在查询每个城市的订单总金额，并按金额从高到低进行排序，从而得出各城市的销售业绩排名。

### 4. 哪个客户消费最高？ — ✅ (重试 0次)
```sql
SELECT u.name AS 客户名称, SUM(o.total_amount) AS 总消费金额
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY 总消费金额 DESC
LIMIT 1
```
**解释**: 这条SQL查询是在找出所有客户中，谁花钱最多，并返回那个消费最高的客户名字和他总共花了多少钱。

### 5. 哪个类别的产品销量最好？ — ✅ (重试 0次)
```sql
SELECT 
    p.category AS 产品类别,
    SUM(o.quantity) AS 总销量
FROM orders o
JOIN products p ON o.product_id = p.id
GROUP BY p.category
ORDER BY 总销量 DESC
LIMIT 1
```
**解释**: 这条SQL查询是在找出所有产品类别中，哪个类别的产品卖出的总数量最多，并只返回销量最高的那个类别。

### 6. 上海的用户有几个？ — ✅ (重试 0次)
```sql
SELECT COUNT(*) AS 用户数量
FROM users
WHERE city = '上海'
```
**解释**: 这句话在统计“用户表”里所有所在城市是“上海”的人一共有多少个，然后显示为一个数字，叫“用户数量”。

### 7. 所有订单总金额是多少？ — ✅ (重试 0次)
```sql
SELECT SUM(o.total_amount) AS 总金额
FROM orders o
```
**解释**: 这条SQL查询是在计算所有订单的金额总和，也就是把每一笔订单的金额加起来，得出一个总的数字。

### 8. 单价最高的产品是什么？ — ✅ (重试 0次)
```sql
SELECT p.name AS 产品名称, p.price AS 单价
FROM products p
ORDER BY p.price DESC
LIMIT 1
```
**解释**: 这条SQL查询是在找出所有产品中**单价最贵的那一个**，并显示出它的名称和价格。

### 9. 2024年6月的订单有多少？ — ✅ (重试 0次)
```sql
SELECT COUNT(*) AS 订单数量
FROM orders
WHERE order_date >= '2024-06-01' AND order_date < '2024-07-01'
```
**解释**: 这句话是在统计2024年6月1日到6月30日之间一共下了多少笔订单，然后告诉你这个数字。

### 10. 销量最低的产品是什么？ — ✅ (重试 0次)
```sql
SELECT p.name AS 产品名称, p.category AS 产品类别, p.price AS 产品价格, p.stock AS 库存数量, COALESCE(SUM(o.quantity), 0) AS 总销量
FROM products p
LEFT JOIN orders o ON p.id = o.product_id
GROUP BY p.id, p.name, p.category, p.price, p.stock
ORDER BY 总销量 ASC
LIMIT 1
```
**解释**: 这条SQL查询是在找出所有产品中**卖得最少（销量最低）的那个产品**，并显示它的名称、类别、价格、库存和总销量。
