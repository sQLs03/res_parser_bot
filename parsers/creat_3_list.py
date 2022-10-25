import logging
import pandas as pd


def get_mean_plot(df) -> list:

    def mean_df(count_plus, count_minus, plus_value, minus_value) -> float:
        return abs(plus_value) * (count_plus / (count_plus + count_minus)) - \
               abs(minus_value) * (count_minus / (count_plus + count_minus))

    cols = ['dBTC', 'dMarket', 'dM24', 'd3h', 'd1h', 'd15m', 'd5m', 'd1m', 'dBTC1m', 'ЕМА', 'ВТС', 'МАvg', 'Max', 'Min',
            'Pump1H']
    res = {
        "Название стратегии": [],
        "Параметр": [],
        "Диапазон": [],
        "Математическое ожидание": []
    }

    for row in cols:
        coin = row

        try:
            df[coin] = df[coin].astype(float)
            sorted_df = df.sort_values(by=coin).reset_index(drop=True)
        except KeyError:
            continue

        step = 0.05

        start = float(sorted_df[coin][0])
        end = float(sorted_df[coin][len(sorted_df[coin]) - 1])
        math_means = []
        distance = []
        list_strat = []
        list_par = []

        while start <= end:
            # Шагаем
            print(start, end)
            two_start = float(start) + float(step)
            two_start = round(two_start, 2)
            strat = ''

            plus_counts, minus_counts, plus_value, minus_value = 0, 0, 0, 0
            for i in range(0, len(sorted_df[coin])):

                line = sorted_df['Comment'][i]
                if line[:20].find("<") != -1:
                    strat = line[line.find("<"):line.find(">") + 1]
                elif line[:50].find(" (") != -1:
                    strat = line[:50].split(" (")[0].split()[-1]
                elif line[:50].find("using strategy") != -1:
                    strat = "#" + line.split("using strategy ")[0].split()[0]
                else:
                    strat = "Названия стратегии в файле не обнаружено"

                if start <= float(sorted_df[coin][i]) <= two_start:

                    h_vol_column, h_vol_value = sorted_df['H. Vol'][i].split(), 0
                    if len(h_vol_column) == 2:
                        if h_vol_column[1] == 'm':
                            h_vol_value = float(h_vol_column[0]) * 1000
                        else:
                            h_vol_value = float(h_vol_column[0])
                    else:
                        h_vol_value = float(h_vol_column[0])

                    try:
                        if float(sorted_df['ProfitUSDT'][i]) >= 0:
                            plus_counts += h_vol_value
                            plus_value += float(sorted_df['ProfitUSDT'][i])

                        else:
                            minus_counts += h_vol_value
                            minus_value += float(sorted_df['ProfitUSDT'][i])
                    except KeyError:
                        if float(sorted_df['ProfitAbs'][i].rstrip()[:-1:]) >= 0:
                            plus_counts += h_vol_value
                            plus_value += float(sorted_df['ProfitAbs'][i].rstrip()[:-1:])

                        else:
                            minus_counts += h_vol_value
                            minus_value += float(sorted_df['ProfitAbs'][i].rstrip()[:-1:])

            if plus_counts + minus_counts != 0:
                math_mean = mean_df(plus_counts, minus_counts, plus_value, minus_value)

            else:
                math_mean = 0
            math_means += [math_mean]
            list_strat += [strat]
            distance += [str(start) + '...' + str(two_start)]
            list_par += [row]

            start += float(step)
            start = round(start, 2)
        res["Параметр"].extend(list_par)
        res["Диапазон"].extend(distance)
        res["Математическое ожидание"].extend(math_means)
        res["Название стратегии"].extend(list_strat)

    res_df = pd.DataFrame.from_dict(res).sort_values(by=["Название стратегии", "Параметр", "Математическое ожидание"], ignore_index=True)
    info_math_list_dict = {}
    index_start = 2
    for index in sorted(res_df["Название стратегии"].value_counts().to_dict().items(), key=lambda item: item[0]):
        index_start_par = index_start
        for index_par in sorted(res_df["Параметр"][index_start - 2:index_start + index[1] - 3].value_counts().
                                       to_dict().items(), key=lambda item: item[0]):
            prom_df = res_df["Математическое ожидание"][index_start_par - 2: index_start_par + index_par[1] - 3]
            info_math_list_dict[index[0], index_par[0]] = [index_start_par]
            for index_math_otr, num in enumerate(prom_df):
                if num >= 0:
                    info_math_list_dict[index[0], index_par[0]].extend([index_math_otr + index_start_par, index_start_par + index_par[1] - 1,
                                                                        res_df["Математическое ожидание"][index_start_par - 2],
                                                                       res_df["Математическое ожидание"][index_start_par + index_par[1] - 3]])
                    break
            if len(info_math_list_dict[index[0], index_par[0]]) == 1:
                info_math_list_dict[index[0], index_par[0]].extend([index_start_par + index_par[1] - 1,
                                                                    res_df["Математическое ожидание"][index_start_par - 2],
                                                                    res_df["Математическое ожидание"][index_start_par + index_par[1] - 3]])
            index_start_par += index_par[1]
        index_start += index[1] + 1
    #print(info_math_list_dict)
    return [res_df, info_math_list_dict]






