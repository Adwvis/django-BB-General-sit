# WITH base_orders AS (
#   SELECT
#     o.id,
#     o.issued_date::date AS date,
#     split_part(u.email, '@', 1) AS national_id,
#     oua.created_date AS assignment_date
#   FROM order_order o
#   JOIN order_userorderassignment oua ON oua.order_id = o.id
#   JOIN auth_user u ON u.id = oua.user_id
#   WHERE o.type = 'thirdparty'
#     AND o.partner_id NOT IN (51, 187, 189)
#     AND u.email ~ '(^|[^0-9])[0-9]{10}([^0-9]|$)'
#     AND o.issued_date BETWEEN '2026-06-21' AND '2026-07-18'
# ),
# has_rayaneh AS (
#   SELECT DISTINCT order_id
#   FROM order_ordercomment
#   WHERE title IN ('رایانه', 'کد رایانه', 'کدرایانه')
# ),
# has_target_state AS (
#   SELECT DISTINCT osl.order_id
#   FROM order_orderstatelog osl
#   JOIN order_transition ot ON ot.id = osl.transition_id
#   WHERE ot.to_state_id IN (42, 58)
# ),
# has_qa_error AS (
#   SELECT DISTINCT order_id
#   FROM order_ordercomment
#   WHERE title ILIKE '%qa%' AND description ILIKE '%error%'
# ),
# has_state_12 AS (
#   SELECT DISTINCT osl.order_id
#   FROM order_orderstatelog osl
#   JOIN order_transition ot ON ot.id = osl.transition_id
#   WHERE ot.to_state_id = 12
# ),
# -- سفارش‌های بدون رایانه (cte1 اصلی)
# no_rayaneh AS (
#   SELECT date, national_id, count(id) AS cnt
#   FROM base_orders b
#   WHERE NOT EXISTS (
#     SELECT 1 FROM order_ordercomment c
#     WHERE c.order_id = b.id
#       AND c.title IN ('رایانه', 'کد رایانه', 'کدرایانه')
#       AND c.created_date < b.date
#       AND c.created_date < b.assignment_date
#   )
#   GROUP BY national_id, date
# ),
# -- سفارش‌های با رایانه و state مناسب (cte2 اصلی)
# with_rayaneh AS (
#   SELECT
#     b.national_id,
#     b.date,
#     count(b.id) AS daily_cnt,
#     sum(count(b.id)) OVER (PARTITION BY b.national_id ORDER BY b.date) AS cumulative_cnt,
#     sum(count(b.id)) OVER (PARTITION BY b.national_id) AS total_cnt
#   FROM base_orders b
#   WHERE EXISTS (
#     SELECT 1 FROM order_ordercomment c
#     WHERE c.order_id = b.id
#       AND c.title IN ('رایانه', 'کد رایانه', 'کدرایانه')
#       AND c.created_date < b.date
#       AND c.created_date < b.assignment_date
#   )
#   AND b.id IN (SELECT order_id FROM has_target_state)
#   GROUP BY b.national_id, b.date
# ),
# combined AS (
#   SELECT
#     w.national_id,
#     w.date,
#     w.daily_cnt + coalesce(n.cnt, 0) AS eff_cnt,
#     w.cumulative_cnt,
#     w.total_cnt
#   FROM with_rayaneh w
#   LEFT JOIN no_rayaneh n ON n.national_id = w.national_id AND n.date = w.date
# ),
# payment_calc AS (
#   SELECT
#     national_id,
#     sum(eff_cnt) AS full_issuance_count,
#     sum(
#       CASE
#         WHEN total_cnt BETWEEN 0 AND 299 THEN
#           eff_cnt * 0.3 * CASE
#             WHEN eff_cnt BETWEEN 0 AND 7   THEN 20000
#             WHEN eff_cnt BETWEEN 8 AND 10  THEN 21000
#             WHEN eff_cnt BETWEEN 11 AND 14 THEN 24000
#             WHEN eff_cnt BETWEEN 15 AND 20 THEN 28000
#             WHEN eff_cnt BETWEEN 21 AND 28 THEN 30000
#             WHEN eff_cnt BETWEEN 29 AND 35 THEN 31000
#             WHEN eff_cnt BETWEEN 36 AND 42 THEN 32000
#             ELSE 39000
#           END
#         WHEN total_cnt BETWEEN 300 AND 399 THEN
#           eff_cnt * CASE
#             WHEN eff_cnt BETWEEN 0 AND 7   THEN 20000
#             WHEN eff_cnt BETWEEN 8 AND 10  THEN 21000
#             WHEN eff_cnt BETWEEN 11 AND 14 THEN 24000
#             WHEN eff_cnt BETWEEN 15 AND 20 THEN 28000
#             WHEN eff_cnt BETWEEN 21 AND 28 THEN 30000
#             WHEN eff_cnt BETWEEN 29 AND 35 THEN 31000
#             WHEN eff_cnt BETWEEN 36 AND 42 THEN 32000
#             ELSE 39000
#           END
#         ELSE -- total >= 400
#           eff_cnt * CASE WHEN cumulative_cnt <= 400 THEN 1.0 ELSE 1.3 END * CASE
#             WHEN eff_cnt BETWEEN 0 AND 7   THEN 20000
#             WHEN eff_cnt BETWEEN 8 AND 10  THEN 21000
#             WHEN eff_cnt BETWEEN 11 AND 14 THEN 24000
#             WHEN eff_cnt BETWEEN 15 AND 20 THEN 28000
#             WHEN eff_cnt BETWEEN 21 AND 28 THEN 30000
#             WHEN eff_cnt BETWEEN 29 AND 35 THEN 31000
#             WHEN eff_cnt BETWEEN 36 AND 42 THEN 32000
#             ELSE 39000
#           END
#       END
#     ) AS full_issuance_payment
#   FROM combined
#   GROUP BY national_id
# ),
# error_count AS (
#   SELECT b.national_id, count(b.id) AS issuance_error_count
#   FROM base_orders b
#   WHERE b.id IN (SELECT order_id FROM has_qa_error)
#     AND b.id IN (SELECT order_id FROM has_state_12)
#   GROUP BY b.national_id
# )
# SELECT
#   p.national_id,
#   p.full_issuance_count,
#   p.full_issuance_payment,
#   coalesce(e.issuance_error_count, 0)::float / p.full_issuance_count AS issuance_error_rate,
#   CASE
#     WHEN p.full_issuance_count BETWEEN 0   AND 180 THEN
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.05  AND 0.075 THEN 0.75 * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.075 AND 0.1   THEN 0.5  * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#     WHEN p.full_issuance_count BETWEEN 181 AND 300 THEN
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.027  AND 0.0405 THEN 0.80 * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.0405 AND 0.054  THEN 0.7  * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#     WHEN p.full_issuance_count BETWEEN 301 AND 450 THEN
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.016 AND 0.024 THEN 0.85  * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.024 AND 0.032 THEN 0.775 * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#     WHEN p.full_issuance_count BETWEEN 451 AND 600 THEN
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.01  AND 0.015 THEN 0.88 * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.015 AND 0.02  THEN 0.82 * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#     WHEN p.full_issuance_count BETWEEN 601 AND 720 THEN
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.007  AND 0.0105 THEN 0.9  * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.0105 AND 0.014  THEN 0.85 * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#     ELSE
#       CASE
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.005  AND 0.0075 THEN 0.92 * p.full_issuance_payment
#         WHEN coalesce(e.issuance_error_count,0)::float/p.full_issuance_count BETWEEN 0.0075 AND 0.01   THEN 0.88 * p.full_issuance_payment
#         ELSE p.full_issuance_payment
#       END
#   END AS full_payment_after_issuance_error
# FROM payment_calc p
# LEFT JOIN error_count e ON e.national_id = p.national_id
