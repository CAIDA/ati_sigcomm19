from __future__ import with_statement
#usage python run_ddc_queries.py >> supplemental_data/multiprocessing_ddc_log.txt 2>&1
#gets list of ipmap files to process from hardcoded list below
#list created by running:
#ls rtt_and_loss_data/rtt/book_keeping/*/*/*ipmap* > supplemental_data/list_of_ipmaps.txt
import matplotlib.pyplot as plt
import matplotlib
import scipy.stats
import os
import sys
import numpy as np
import bz2

cc_filename = "/project/mapkit/agamerog/country_asn_analysis/cc_to_name_eng.csv"
snapshot = str(sys.argv[1])
snapshot2 = str(sys.argv[2])
#UN_filename = "/project/mapkit/agamerog/country_asn_analysis/list_of_country_codes.txt"
#countries = ['AF','AL','DZ','AD','AO','AG','AR','AM','AU','AT','AZ','BS','BH','BD','BB','BY','BE','BZ','BJ','BT','BO','BA','BW','BR','BN','BG','BF','BI','CV','KH','CM','CA','CF','TD','CL','CN','CO','KM','CG','CD','CR','CI','HR','CU','CY','CZ','DK','DJ','DM','DO','EC','EG','SV','GQ','ER','EE','ET','FJ','FI','FR','GA','GM','GE','DE','GH','GR','GD','GT','GN','GW','GY','HT','VA','HN','HU','IS','IN','ID','IR','IQ','IE','IL','IT','JM','JP','JO','KZ','KE','KI','KP','KR','KW','KG','LA','LV','LB','LS','LR','LY','LI','LT','LU','MK','MG','MW','MY','MV','ML','MT','MH','MR','MU','MX','FM','MD','MC','MN','ME','MA','MZ','MM','NR','NP','NL','NZ','NI','NE','NG','NO','OM','PK','PW','PS','PA','PG','PY','PE','PH','PL','PT','QA','RO','RU','RW','KN','LC','VC','WS','SM','ST','SA','SN','RS','SC','SL','SG','SK','SI','SB','SO','ZA','SS','ES','LK','SD','SR','SZ','SE','CH','SY','TJ','TZ','TH','TL','TG','TO','TT','TN','TR','TM','TV','AE','UG','GB','UA','UY','US','UZ','VU','VE','VN','YE','ZM','ZW']

#countries =['BJ', 'CN', 'RU', 'US', 'ZA']
countries =['US']
plot_filename = "/project/mapkit/agamerog/country_asn_analysis/plots/gdp_scatter.pdf"

asrel_filename = '/project/mapkit/agamerog/country_asn_analysis/20180301.as-rel.txt'

os.system('ulimit -d 30000000; ulimit -m 30000000; ulimit -v 30000000')


def read_astypes():
    AT = open('/project/mapkit/agamerog/country_asn_analysis/20180301.as2types.txt', 'rb')
    ATdict = {}
    for lines in AT:
        if len(lines) > 0 and lines[0] != '#':
            ASnumstr = int(lines.split('|')[0]) #grab ASN
            AStype = str(lines.split('|')[2])
            if 'Transit' in AStype:
                ATdict[ASnumstr] = 0
            elif 'Content' in AStype:
                ATdict[ASnumstr] = 1
            else:
                ATdict[ASnumstr] = 3
    AT.close()
    return ATdict

def read_asrel_file():
    asrel_set = set()
    with open (asrel_filename,'rb') as f:
        rows = f.readlines()
        for i in range(len(rows)):
            if '#' in rows[i]:
                continue
            row = rows[i].strip('\n')
            row_rel = row.split('|')[2]
            if int(row_rel) != -1:
                continue
            else:
                provider = row.split('|')[0]
                customer = row.split('|')[1]
                p2c = provider + ':' + customer
                asrel_set.add(p2c)
        return asrel_set

def read_cc(filename):
    cc_dict = {}
    with open (filename,'rb') as f:
        rows = f.readlines()
        for i in range(len(rows)):
            cc = rows[i].split(',')[1]
            name = rows[i].split(',')[0]
            cc_dict[cc] = name
        return cc_dict

def read_filter():
    cc_filter = set()
    with open (filter_filename,'rb') as f:
        rows = f.readlines()
        for i in range(len(rows)):
            row = rows[i].strip('\n')
            cc_filter.add(row)
    return cc_filter

def fetch_asname(asn, asname_dict):
    try:
        line = asn + '-' + asname_dict[asn]
    except KeyError:
        line = asn + '-unknown'
    return line

def systemCall(parameter):
    os.system(parameter)

def read_origin_file(country):
    origin_dict = dict()
    addy_dict = dict()
    origin_filename = "/project/mapkit/agamerog/country_asn_analysis/country_aspath/origin/" + snapshot + "/" + country + ".csv.bz2"
    with bz2.BZ2File(origin_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if '#' in row:
                continue #skip header #AGG need to automate skipping headers
            transit_rank = float(row.split(',')[2])
            asn = row.split(',')[0].split('-')[0]
            addresses = int(float(256) * float(row.split(',')[1]))
            origin_dict[asn] = transit_rank #this one has percentage of origin addresses
            #print str(country) + "\t" + str(transit_rank)
            addy_dict[asn] = addresses

    return origin_dict, addy_dict

def read_top_file(country, month):
    
    output_dict = dict()
    reverse_output_dict = dict()
    if '.tr' in month:
        origin_filename = "/project/mapkit/agamerog/country_asn_analysis/country_aspath/" + month.replace('.tr','') + "/top." + country + ".tr.csv.bz2"
    else:
        origin_filename = "/project/mapkit/agamerog/country_asn_analysis/country_aspath/" + month.replace('.tr','') + "/top." + country + ".csv.bz2"
    with bz2.BZ2File(origin_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        j = 1
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if '#' in row:
                continue #skip header #AGG need to automate skipping headers
            rank = j
            asn = int(row.split(',')[3].split('-')[0])
            output_dict[rank] = asn
            reverse_output_dict[asn] = rank
            j = j+1

            #break
        return output_dict, reverse_output_dict

def read_summary_file():
    country_dict = dict()
    
    summary_filename = "/home/agamerog/influenceimc18/country_influence_imc18/data/country/country_info_no_note.csv"
    with open(summary_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if i == 0:
                continue #skip header #AGG need to automate skipping headers
            if '#' in row:
                continue
            code = row.split(',')[0]
            addies = int(row.split(',')[3])
            country_dict[code] = addies
        return country_dict

def read_gdp_file():
    country_dict = dict()
    
    summary_filename = "WITS-Country.csv"
    with open(summary_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        #print "IM HERE"
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if i == 0:
                continue #skip header #AGG need to automate skipping headers
            #print "IM HERE"
            code = row.split(',')[1]
            gdp = float(row.split(',')[2])/float(1000)
            country_dict[code] = gdp
        #print country_dict
        return country_dict



def read_transit_file(country, origin_dict):
    transit_dict = dict()
    customer_addy = dict()
    dominated_set = set()
    parsed_origins = set()
    transit_sum = 0.0 #addresses originated by the transit provider as long as they have not been counted as origin
    origin_sum = 0.0
    transit_filename = "/project/mapkit/agamerog/country_asn_analysis/country_aspath/" + snapshot + "/ext." + country + ".csv.bz2"

    with bz2.BZ2File(transit_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if '#' in row:
                continue #skip header #AGG need to automate skipping headers
            transit_influence = round(float(row.split(',')[4]),2)
            if transit_influence < 0.5:
                continue #ignore non-heavy-reliant
            
            transit_rank = float(row.split(',')[7])
            asn_origin = row.split(',')[3].split('-')[0]
            dominated_set.add(asn_origin)
            if asn_origin in origin_dict:
                if asn_origin not in customer_addy:
                    customer_addy[asn_origin] = origin_dict[asn_origin] #save number of addresses originated 
                if asn_origin not in parsed_origins:
                    origin_sum = origin_sum + origin_dict[asn_origin]
                    parsed_origins.add(asn_origin)

            asn_transit = row.split(',')[2].split('-')[0]
            #if asn_transit not in transit_dict:
            #    if asn_transit in origin_dict:
            #        transit_dict[asn_transit] = origin_dict[asn_transit]
            #        if asn_transit not in parsed_origins:
            #            transit_sum = transit_sum + origin_dict[asn_transit]
            #            parsed_origins.add(asn_transit)
        dom_ases = len(dominated_set)

    return dom_ases, origin_sum, transit_sum

def read_customer_file():
    customer_dict = dict()
    customer_filename = "/project/comcast-ping/stabledist/mapkit/code/AnnouncedPrefixesMatrix/LPM2/AlexSummaryINVERSO/TOPk100ASes_rowsum_" + current_country + ".csv" 
    with open(customer_filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
        
        for i in range(len(ipmap_list)):
            row = ipmap_list[i].strip('\n')
            if 'T' in row:
                continue #skip header #AGG need to automate skipping headers
            transit_rank = float(row.split(',')[2])
            asn = row.split(',')[0]
            customer_dict[asn] = transit_rank

    return customer_dict



def read_asname():

    AS = open('/home/agamerog/plots/ddc/AS-table.txt', 'rU')
    ASdict = {}
    for lines in AS:
        if len(lines) > 0 and lines[0] == 'A':
            ASnumstr = lines.split()[0][2:] #throw away the AS
            AStextlist = lines.split()[1:10]
            AStextlist = " ".join(AStextlist).replace(',','')
            AStextlist = AStextlist[:12]
            #ASdict[ASnumstr] = " ".join(AStextlist).replace(',','')
            ASdict[ASnumstr] = AStextlist
    AS.close()
    return ASdict

def plot_origin_transit(country_numbers, country_dict, country_ases, cc_dict, gdp_dict):
    output_file = "/project/mapkit/agamerog/country_asn_analysis/all_countries_ases_addresses_dominated.csv"
    font = {'family' : 'Times New Roman', 'weight' : 'bold', 'size'   : 13}
    matplotlib.rc('font', **font)
    fig = plt.figure(1, figsize=(16,16))
    colors = ['k','b','y','g','r']
    ax = fig.add_subplot(1, 1, 1)
    plotx = []
    ploty = []
    i = 0
    yorigin = 0.08
    already_colored = set()
    low_ases = [] 
    low_addies = []
    mid_ases = [] 
    mid_addies = []
    hi_ases = [] 
    hi_addies = []
    legend = True
    xx = []
    y1 = []
    y2 = []
    #with open (output_file,'w+') as f:
        #f.write('cc,perc_ases,perc_origin_addresses_customers,perc_origin_addreses_incl_originated_by_transit\n')
    for country in country_numbers:

        dom_ases = country_numbers[country][0]
        total_ases = country_ases[country]
        try:
            z = gdp_dict[country]
        except KeyError:
            print ("no GDP data for " + str(cc_dict[country]))
            z = 1000
            continue
        x = float(100) * float(dom_ases) / float(total_ases)
        #y = country_numbers[country][1]

        y = country_numbers[country][1]
        #f.write(country + ',' + str(x) + ',' + str(y) + ',' + str(z) + '\n')
        
        ax.set_ylabel('Heavily Reliant ASes and their Originated Add., \nPerc. of Country (log scale)', fontsize = 32)
        #ax.set_xlabel('GDP Per Capita', fontsize = 18)a
        
        ax.set_xlabel('GDP Per Capita (log scale)', fontsize = 32)
        csize = z 
        y1.append(x)
        y2.append(y)
        xx.append(csize)
        #if legend == True:

            #ax.scatter(csize,x, color='r', alpha = 0.7, label = 'Percentage of ASes')
            #ax.scatter(csize,y, color='b', alpha = 0.7, label = 'Percentage of Addresses')
            #legend = False
        #else:
            #ax.scatter(csize,x, color='r', alpha = 0.7)
            #ax.scatter(csize,y, color='b', alpha = 0.7)
    y1s = [x for _,x in sorted(zip(xx,y1))]
    y2s = [x for _,x in sorted(zip(xx,y2))]
    xxs = sorted(xx)
    ax.plot(xxs,y1s,color='r', marker = "o", markersize = 5, lw=2, alpha = 0.7, label = 'Percentage of ASes')
    ax.plot(xxs,y2s,color='b',marker = "o", markersize = 5, lw=2, alpha = 0.7, label = 'Percentage of Addresses')
    ax.set_title('AS and Address Concentration \n Across Countries vs. GDP Per Capita \nn=188 UN Members with GDP Per Capita Info', fontsize = 26)
    ax.set_xlim([200, 180000])
    ax.set_ylim([1, 102])
    ax.set_yscale('log')
    ax.legend(loc=3,fontsize=28)
    plt.tight_layout()
    ax.set_xscale('log')
    z = np.polyfit(xxs, y2s, 1)
    p = np.poly1d(z)
    ax.plot(xxs,p(xxs),"r--")
    # the line equation:
    print "y=%.6fx+(%.6f)"%(z[0],z[1])

    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(xxs, y2s)
    print( 'r2 ' + str(r_value*r_value))
    print( 'p ' + str(p_value))
    print('stderr ' + str(std_err))
    print('slope' + str(slope))
    print( ' intercept ' + str(intercept))
    fig.savefig(plot_filename)
    #addie_reg = []
    #gdp_reg = []
    #for i in range(len(xxs)):
    #    addie_reg.append(np.log10(y2s[i]))
    #    gdp_reg.append(np.log10(y2s
    # calc the trendline

def read_ipmap(filename):
    #read ipmap lines into list
    ipmap_list = ''
    with open(filename, 'rb') as f: #import file
        ipmap_list = f.readlines()
    return ipmap_list

def main():

    asrel_set = read_asrel_file()

    cc_dict = read_cc(cc_filename)
 
    asname_dict = read_asname() #read asnames into memory
    
    country_dict = read_summary_file()

    gdp_dict = read_gdp_file()
    ignored_countries = set()

    #country_ases = dict()

    #second_country_ases = dict()

    country_numbers = dict() #numbers to plot on scatter
 
    print "#country,identical_count,intersec_size,avg_change,unranked_first,unranked_second"
    printed_countries = 0

    for i in range(len(countries)):
        
        country = countries[i]
        #ignored_countries = set()
        #print country
        country_ases = dict()
        reverse_country_ases = dict() #reverse dict with key = asn and value = rank
        second_country_ases = dict()
        reverse_second_country_ases = dict()

        country_ases, reverse_country_ases = read_top_file(country, snapshot)
        second_country_ases, reverse_second_country_ases = read_top_file(country, snapshot2)
        if len(country_ases) <10 or len(second_country_ases) < 10:
            ignored_countries.add(country)
            #print ("ignoring country because fewer than 10 ASes " + country )
            continue
        else:
            printed_countries = printed_countries + 1

        remained = set() #set of asns that did not change rank
        remained_count = 0 #number of ASes that did not change rank
        rank_change_list = []
        first_month_set = set()
        second_month_set = set()
        unranked_first = 0
        unranked_second = 0
        num_analyze = 10
        min_change = 2

        boundaries = {1:10,11:20,21:30,31:50,51:100}
        for boundary in boundaries:
            rank_change_list = []
            initial = boundary
            final = boundaries[boundary]
            i = initial
            while i <= final:
                curr_rank = i
                if country_ases[curr_rank] == second_country_ases[curr_rank]:
                    remained_count = remained_count + 1
                    remained.add(country_ases[curr_rank])
                else:
                    if country_ases[curr_rank] in reverse_second_country_ases:
                        curr_change = abs(reverse_country_ases[country_ases[curr_rank]] - 
                            reverse_second_country_ases[country_ases[curr_rank]])
                        #print curr_change
                        rank_change_list.append(curr_change)
                        remained.add(country_ases[curr_rank])
                    else:
                        unranked_second = unranked_second + 1
                first_month_set.add(country_ases[curr_rank])
                second_month_set.add(second_country_ases[curr_rank])
                i = i + 1

            i = initial
            while i <= final:
                curr_rank = i 
                if second_country_ases[curr_rank] not in remained: #ASes not in top 10 of first month
                    if second_country_ases[curr_rank] in reverse_country_ases:
                        #print "first rank = " + str(reverse_country_ases[second_country_ases[curr_rank]]) 
                        #print "second rank = " + str(reverse_second_country_ases[second_country_ases[curr_rank]])
                        #print "difference = " 

                        curr_change = abs(reverse_country_ases[second_country_ases[curr_rank]] - reverse_second_country_ases[second_country_ases[curr_rank]])
                        #print curr_change
    
                        rank_change_list.append(curr_change)
                    else:
                        unkranked_first = unranked_first + 1
                i = i + 1
            #print (rank_change_list)
            intersection_number = len(first_month_set.intersection(second_month_set))
            #print (first_month_set.difference(second_month_set))
            #print first_month_set
            #print second_month_set
            rank_change_list.sort()
            length = len(rank_change_list)
            print (str(initial) + ',' + str(final) + ',' + str(rank_change_list[length-1]) + ',' + str(rank_change_list[length-2]))

        #country_addresses = country_dict[country]

        #origin_dict, addy_dict = read_origin_file(country)
        #try:

        #    dom_ases, origin_sum, transit_sum = read_transit_file(country, origin_dict)
        
        #except IOError:
        #    continue
        #country_numbers[country] = [dom_ases, origin_sum, transit_sum]
    print ("# " + str(len(ignored_countries)) + "\t" + str(ignored_countries))
    print ("# analyzed countries " +str(printed_countries))
    #customer_dict = read_customer_file()
    
    #plot_origin_transit(country_numbers, country_dict, country_ases, cc_dict, gdp_dict)
    #print origin
    #print transit
main()
#print ("saving /project/mapkit/agamerog/country_asn_analysis/all_countries_ases_addresses_dominated.csv")
#print ("saving " + plot_filename)
