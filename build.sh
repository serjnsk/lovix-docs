#!/bin/bash
# Сборка index.html из MODULE_1_tokenomics.md и HTML-частей.
# Запуск: bash site/build.sh (из корня lovix_alerts)
set -e
cd "$(dirname "$0")"
MD="MODULE_1_tokenomics.md"

awk '!f; /^## 1\. Тарифы/{f=1}' "$MD" | sed '$d'            > /tmp/lovix_md0.md
awk '/^## 1\. Тарифы/{f=1} /^## 2\. Пакеты/{f=0} f' "$MD"    > /tmp/lovix_md1.md
awk '/^## 2\. Пакеты/{f=1} /^## 3\. Прайс/{f=0} f' "$MD"     > /tmp/lovix_md2.md
awk '/^## 3\. Прайс/{f=1} f' "$MD"                           > /tmp/lovix_md3.md

cat _p0_head.html /tmp/lovix_md0.md \
    _p1_sep.html  /tmp/lovix_md1.md \
    _p2_sep.html  /tmp/lovix_md2.md \
    _p3_sep.html  /tmp/lovix_md3.md \
    _p4_tail.html > index.html

cat _m_head.html MODULE_2_metrics.md _m_foot.html > metrics.html
cat _e_head.html MODULE_3_events.md _m_foot.html > events.html
cat _n_head.html MODULE_4_scenarios.md _m_foot.html > scenarios.html

echo "index.html собран: $(wc -c < index.html) байт"
echo "metrics.html собран: $(wc -c < metrics.html) байт"
echo "events.html собран: $(wc -c < events.html) байт"
echo "scenarios.html собран: $(wc -c < scenarios.html) байт"
