import tsgauth
import requests
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import numpy as np

def calculate_standard_deviation(base, target, base_err, target_err):
    term1 = target*target*base_err*base_err/(base**4)
    term2 = target_err*target_err/(base*base)
    return (term1 + term2)**0.5

if __name__ == "__main__":
    auth = tsgauth.oidcauth.DeviceAuth("cms-tsg-frontend-client",use_auth_file=True)

    r_results = requests.get("https://timing-gui-api-tsg-steam.app.cern.ch/v0/timing/list_results",**auth.authparams())

    results = r_results.json()["results"]

    tag_list = ['ebet5_eeet6', 'ebet5_eeet7', 'ebet5_eeet8', 'ebet5_eeet9', 'ebet5_eeet10', 
                'ebet5_eeet5', 'ebet6_eeet6', 'ebet7_eeet7', 'ebet8_eeet8', 'ebet9_eeet9',
                'ebet10_eeet10']
    
    x = [int(tag.split('_')[1].replace('eeet','')) for tag in tag_list]
    y = [0]*len(x)
    y_sd = [0]*len(x)

    pt = PrettyTable()
    pt.field_names = ["Tag", "Throughput (evt/s)", "Gain (%)"]

    throughput_base = [r["job_result"]["throughput"]["value"] 
                       for r in results if r["job_cfg"]["current_user"] == "asahasra" 
                       and r["job_start_time"].startswith("Thu, 18 Apr 2024")
                       and r["job_cfg"]["job_id"].startswith("CMSSW_14_0_1") 
                       and 'base2' in r["job_cfg"]["job_id"]]
    throughput_base_err = [r["job_result"]["throughput"]["error"] 
                           for r in results if r["job_cfg"]["current_user"] == "asahasra"
                            and r["job_start_time"].startswith("Thu, 18 Apr 2024")
                            and r["job_cfg"]["job_id"].startswith("CMSSW_14_0_1")
                            and 'base2' in r["job_cfg"]["job_id"]]

    pt.add_row(["base2", f'{round(throughput_base[0], 2)} ± {round(throughput_base_err[0], 2)}', "--"])

    for tag in tag_list:
        results_tag = [r for r in results if r["job_cfg"]["current_user"] == "asahasra" 
                       and r["job_start_time"].startswith("Thu, 18 Apr 2024")
                       and r["job_cfg"]["job_id"].startswith("CMSSW_14_0_1") 
                       and tag in r["job_cfg"]["job_id"]]

        throughput = [r["job_result"]["throughput"] for r in results_tag if "job_result" in r]
        throughput_avg = sum([t["value"] for t in throughput])/len(throughput)
        
        tput_diff = np.array([t["value"] for t in throughput]) - throughput_avg
        throughput_err = sum(tput_diff*tput_diff)/len(tput_diff)

        gain = throughput_avg*100/throughput_base[0] - 100
        gain_sd = calculate_standard_deviation(throughput_base[0], 
                                               throughput_avg, 
                                               throughput_base_err[0], 
                                               throughput_err)
        gain_sd = gain_sd*100

        y[tag_list.index(tag)] = gain
        y_sd[tag_list.index(tag)] = gain_sd

        pt.add_row([tag, f'{round(throughput_avg, 2)} ± {round(throughput_err, 2)}', 
                    f'{round(gain, 2)} ± {round(gain_sd, 2)}'])

    print(pt)

    plt.scatter(x[0:5], y[0:5], marker='o', label='$E_{B} > 5$ GeV and $E_{E} > E_{T}$')
    plt.errorbar(x[0:5], y[0:5], yerr=y_sd[0:5], fmt='--', capsize=5)
    plt.scatter(x[5:], y[5:], marker='*', label='$E_{B} > E_{T}$ and $E_{E} > E_{T}$')
    plt.errorbar(x[5:], y[5:], yerr=y_sd[5:], fmt='--', capsize=5)

    plt.xlabel('$E_{T}$ threshold [GeV]')
    plt.ylabel('Throughput gain (%)')

    plt.legend()

    plt.savefig('throughput_gain.png')

    #ar_results = [r for r in results if r["job_cfg"]["current_user"] == "asahasra" and r["job_cfg"]["job_id"].startswith("CMSSW_14_0_1_us")]

    #for result in ar_results:
        #throughput = result["job_result"]["throughput"] if "job_result" in result else None
        #if throughput is not None:
            #print(f'{result["job_cfg"]["job_id"]} : {throughput["value"]} ± {throughput["error"]}')
