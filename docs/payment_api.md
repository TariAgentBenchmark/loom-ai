API文档

基础支付

聚合收银台

公共参数
公共参数
更新时间：2024-12-02 18:04:02
作者：wanghuiling
公共说明
接口文档中，必选栏目：M 必须，C 可选

说明	描述
接口版本	v1.0.0
功能描述	外部机构接入开放平台
调用方	外部机构
请求方法	POST
请求签名	是
响应签名	是
需要BASE64编码	否
授权方式	
测试环境URL	https://test.wsmsd.cn/sit/xx
生产环境URL	https://xxxx/xx


公共请求参数
字段	说明	是否必填	类型	备注
req_time	请求时间	M	String(14)	请求时间，格式yyyyMMddHHmmss
version	版本号	M	String(8)	1.0
req_data	请求参数	M	Object	


公共响应参数
属性	说明	必选	类型	备注
code	返回业务代码	M	String(8)	返回业务代码(000000为成功，其余按照错误信息来定)
msg	返回业务代码描述	M	String(64)	返回业务代码描述
resp_time	响应时间	M	String(14)	响应时间，格式yyyyMMddHHmmss
resp_data	响应参数	C	Object	返回数据.下文定义的响应均为该属性中的内容


收银台订单创建
更新时间：2025-10-29 14:08:33
作者：wanghuiling
调用地址
注：因银网联测试环境问题，微信钱包在测试环境下无法下单完成支付，下单后提示”sub mch id与sub appid不匹配”报错即可。

自2024年1月16日起，请通过以下接口进行接入：

使用HTTP协议，POST方式提交。

URL(测试环境外网)：https://test.wsmsd.cn/sit/api/v3/ccss/counter/order/special_create

URL(生产环境)：https://s2.lakala.com/api/v3/ccss/counter/order/special_create

商户需在微信商家后台配置以下支付域名（原支付目录），2023 年 9 月后入网的商户可忽略此配置：

生产环境订单域名：pay.lakala.com

测试环境订单域名：pay.wsmsd.cn

请求参数
字段名	是否必输	类型	长度	字段描述	示例
out_order_no	M	String	32	商户订单号	12345678
merchant_no	M	String	32	银联商户号	822100041120005
vpos_id	C	String	32	交易设备标识，进件返回接口中的termId字段，非API接口进件请联系业务员。	462621830268882944
channel_id	C	String	32	渠道号 （一般不用）	24865454154
total_amount	M	long	12	订单金额，单位：分	200
order_efficient_time	M	String	14	订单有效期 格式yyyyMMddHHmmss,最大支持下单时间+7天	20210803141700
notify_url	C	String	128	订单支付成功后商户接收订单通知的地址 http://xxx.xxx.com	
support_cancel	C	int	1	是否支持撤销 默认 0 不支持
busi_mode为“PAY-付款”不支持 撤销	（0 不支持 1支持）
support_refund	C	int	1	是否支持退款 默认0 不支持	（0 不支持 1支持）
support_repeat_pay	C	int	1	是否支持“多次发起支付” 默认0 不支持	（0 不支持 1支持）
out_user_id	C	String	64	发起订单方的userId，归属于channelId下的userId	
callback_url	C	String	128	客户端下单完成支付后返回的商户网页跳转地址。	
order_info	M	String	64	订单标题，在使用收银台扫码支付时必输入，交易时送往账户端	
term_no	C	String	32	结算终端号,合单场景必输该字段	
split_mark	C	String	2	合单标识，“1”为合单，不填默认是为非合单	
settle_type	C	String	4	
结算类型（非合单） （“0”或者空，常规结算方式）
  注意：该字段会影响结算方式，慎用。（调用拉卡拉分账接口，分账模式为标记分账时需必传1）


out_split_info	C	List<>	
拆单信息
合单标识为“1”时必传该字段。,详细字段见out_split_info字段说明	
counter_param	C	String	1024	json字符串 收银台展示参数	{\“pay_mode\“ : \“ALIPAY\“} ，指定支付方式为支付宝
ALIPAY：支付宝
WECHAT：微信
UNION：银联云闪付
CARD：POS刷卡交易
LKLAT：线上转帐
QUICK_PAY：快捷支付
EBANK：网银支付
UNION_CC：银联支付
BESTPAY：翼支付
HB_FQ：花呗分期
UNION_FQ：银联聚分期

ONLINE_CARDLESS：线上外卡

若要指定支付方式为支付宝传参格式：
{\“pay_mode\“ : \“ALIPAY\“}

counter_remark
C	String	128	收银台备注	
busi_type_param	C	String	256	业务类型控制参数，jsonStr格式	[{\“busi_type\“:\“UPCARD\“,\“params\“:{\“crd_flg\“:\“CRDFLG_D|CRDFLG_C|CRDFLG_OTH\“}},{\“busi_type\“:\“SCPAY\“,\“params\“:{\“pay_mode\“:\“ALIPAY\“,\“crd_flg\“:\“CRDFLG_D\“}}]
说明：UPCARD-刷卡，SCPAY-扫码，CRDFLG_D-借记卡，CRDFLG_C-贷记卡，CRDFLG_OTH-不明确是借记卡还是贷记卡
pay_mode送参说明：ALIPAY-支付宝，WECHAT-微信，UNION-银联二维码，DCPAY-数字货币，BESTPAY-翼支付
说明：一旦使用该字段，则增加限制，必须在指定限制范围内支付。比如，只配置”busi_type”:”UPCARD”的参数而不配置”busi_type”:”SCPAY”的参数，则只能通过刷卡而不能通过扫码完成支付

sgn_info	C	list<>	
签约协议号列表（字符串）	[“1234”,”2345”]，不支持空列表[]；列表中签约协议号不能为空；列表中签约协议号不能重复
product_id
C	String	6	指定产品编号 （200809:线上外卡收银台） 注意：该字段默认不需要指定，特殊场景下使用，慎用	
goods_mark	C	String	
商品信息标识 （1:含商品信息，不填默认不含商品信息）	
goods_field	C	String	2	商品信息域(good_mark送1时该域必填，否则不送。只有线上外卡业务上送该字段) 详细字段见goods_field字段说明	
order_scene_field	C	Object
2	订单场景域，特殊场景下需要上送 详细字段见order_scene_field字段说明	
age_limit	C	String	1	0:不限年龄；1:年龄限制	
repeat_pay_auto_refund	C	String	1	
0:重复支付后不自动退货；1:重复支付后自动退货 （默认不送为0），注意：请详细了解字段场景后上送

需注意互斥条件：repeat_pay_auto_refund选择“1”重复支付后自动退货后，repeat_pay_notify仅支持选择“0”重复支付订单不通知


repeat_pay_notify	C	String	1	0:重复支付订单不通知；1:重复支付订单通知 （默认不送为0）	
close_order_auto_refund	C	String	1	0:不自动退货；1:关闭订单后支付成功触发自动退货 （默认不送为0）注意：请详细了解字段场景后上送	
shop_name	C	String	64	网点名称	
inte_routing	C	String	2	智能路由下单标识 1-是 0-否（默认不送为0）备注：需要在收银台管控台配置聚合收银台小程序白名单	
discount_code	C	String	64	优惠码(目前供线上国补下单使用)	
electrical_equipment_category	C
String
128	支付宝优惠码(目前优惠码的地区：浙江、江苏、上海、福建、重庆)	
trade_biz_tp	C	String	16	线上业务通道类型	具体类型见补充枚举
out_split_info字段说明
字段名	中文名称	是否必填	类型	说明
out_sub_order_no	外部子订单号	M	String(32)	商户子订单号
merchant_no	商户号	M	String(32)	拉卡拉分配的银联商户号
term_no	终端号	M	String(32)	拉卡拉分配的业务终端号
amount	金额	M	String(12)	单位分，整数型字符
settle_type	结算类型（合单）	C	String(4)	“0”或者空，常规结算方式
说明：

 1）拆单信息域中商户号不可重复；

 2）交易层订单金额必须是拆单信息域中各个子单的金额汇总之和；

 3）对拆单信息域中每个结算商户号和终端号的权限交易都必须通过，其中一个校验失败，则交易中止，失败返回；

 4）拆单域中子单条数最少两条、最多20条，否则拒绝。

goods_field字段说明
字段名	中文名称	是否必填	类型	说明
goods_amt	商品单价	M	Long	单位：分
goods_num	商品数量	M	Integer	
goods_pricing_unit	商品计价单位	M	String(8)	1-箱 2-件 3-瓶 4-个
goods_name	商品名称	M	String(128)	
te_platform_type	交易电商平台类型	M	String(2)	1-境内平台 2-境外平台
te_platform_name	交易电商平台名称	M	String(256)	
goods_type	交易商品类型	M	String(8)	1:服饰箱包
2:食品药品
3:化妆品
4:电子产品
5:日用家居
7:航空机票
8:酒店住宿
9:留学教育
10:旅游票务
11:国际物流
12:国际租车
13:国际会议
14:软件服务
15:医疗服务
16:通讯
17:休闲娱乐
order_scene_field字段说明
字段名	中文名称	是否必填	类型	说明
order_scene_type	订单场景类型	M	String(16)	订单场景类型（按下述定义场景送值）
HB_FQ：花呗分期场景

KL_FQ：考拉分期场景

scene_info	订单场景信息	C	String(1024)	订单场景信息（json字符串格式），不同的订单场景类型需要上送的结构不一样（详见具体场景）
HB_FQ场景
scene_info字段说明
字段名	中文名称	是否必填	类型	说明
hbFqNum	花呗分期期数	M	String	支付宝花呗分期必送字段: 花呗分期数 3：3期 6：6期 12：12期
hbFqSellerPercent	卖家承担手续费比例	M	String	支付宝花呗分期必送字段: 卖家承担手续费比例，间连模式下只支持传0。
JDBT场景
scene_info字段说明
字段名	中文名称	是否必填	类型	说明
LOCKPLAN	

String	
->jdbtFqNum	京东白条分期期数	M	String	京东白条分期数 3：3期，6：6期，12：12期 ，24：24期
trade_biz_tp字段说明
拉卡拉业务种类编码	编码含义
100001	虚拟商品购买
100002	预付费类账户充值
100003	实物消费
100004	航空商旅消费
100005	生活及商业服务消费
100006	其他商户消费
100007	招投标保证金支付
100008	境外商品购买
100A01	实物商品租赁
100A03	单用途预付卡充值
100A06	商业服务消费
100A05	航旅交通服务
100A07	生活服务消费
100A08	个人经营服务
110001	公共事业缴费
110002	教育医疗缴费
110003	政府服务缴费
110004	公益捐款
110005	农林牧副渔收购
110006	政府服务
110007	薪资发放
110008	其他公共服务
110A01	水电煤气缴费
110A02	税费缴纳
110A03	非营利性教育缴费
110A05	罚款缴纳
110A06	路桥通行缴费
110A07	邮政缴费
110A08	电视账单缴费
110A09	话费账单缴费
110A10	宽带账单缴费
110A13	财政非税收入
110A14	营利性教育培训
110A15	公共交通
110A16	急救救援
110A17	物业缴费
110A18	国库经收
110A19	供暖费缴纳
110A20	废弃物处理费用缴纳
110A21	租金缴纳
110A22	会员费用缴纳
110A23	税费退还
120001	其他金融付款
120002	其他金融收款
120003	基金购买
120004	保险选购
120005	投资理财
120006	信贷偿还
120007	信用卡还款转出
120008	基金赎回/返还/分红
120009	保险理赔/分红
120010	投资理财赎回/返还/分红
120011	信贷发放
120012	信用卡还款转入
120A01	基金理财产品申购
120A02	基金理财产品认购
120A03	非投资型保险费用缴纳
120A05	商业众筹
120A06	贵金属投资买入
120A07	基金理财产品赎回
120A08	基金理财产品到期返还
120A09	认/申购失败返还
120A10	基金理财产品分红
120A11	保险理赔或退费
120A12	保险红利发放或给付发放
120A13	贵金属投资买出
120A16	融资租赁
120A19	投资型保险费用缴纳
120A20	小贷公司贷款还款
120A21	保单贷款发放
120A22	其他保险资金代发
130001	支付账户充值
130002	支付账户回提
130003	银行账户转账转出
130004	其他账户充值
130005	银行账户转账转入
130006	其他账户回提
130A03	向他人支付账户转账
130A05	预付卡赎回 -个人赎回
130A06	预付卡赎回-单位赎回
130A08	测试验证资金
130A09	薪酬福利发放
130A10	代发货款
140001	商户结算-交易资金结算
140002	营销返现
140003	其他商户结算
140A02	预付卡商户结算
140A03	商户收单资金提现
150A01	资金归集
200000	对公业务


请求样例
{
    "req_data": {
        "out_order_no": "KFPT20220714160009228907288", 
        "merchant_no": "8222900701106PZ", 
        "vpos_id": "587305941625155584", 
        "channel_id": "2021052614391", 
        "total_amount": "1", 
        "order_efficient_time": "20220714170009", 
        "notify_url": "http://run.mocky.io/v3/b02c9448-20a2-4ff6-a678-38ecab30161d", 
        "support_cancel": "0", 
        "support_refund": "1", 
        "support_repeat_pay": "1", 
        "busi_type_param": "[{\"busi_type\":\"UPCARD\",\"params\":{\"crd_flg\":\"CRDFLG_D|CRDFLG_C|CRDFLG_OTH\"}},{\"busi_type\":\"SCPAY\",\"params\":{\"pay_mode\":\"WECHAT\",\"crd_flg\":\"CRDFLG_D\"}}]", 
        "counter_param": "{\"pay_mode\":\"ALIPAY\"}", 
        "out_user_id": "", 
        "order_info": "自动化测试", 
        "extend_info": "自动化测试", 
        "callback_url": ""
    }, 
    "version": "3.0", 
    "req_time": "20220714160009"}
复制
返回参数
字段名	是否必输	类型	长度	字段描述	示例
merchant_no	M	String	32	
银联商户号
channel_id	M	String	32	

out_order_no	M	String	32	商户订单号	
order_create_time	M	String	32	创建订单时间	订单系统创建订单的时间，格式yyyyMMddHHmmss
order_efficient_time	M	String	32	订单有效截至时间	格式yyyyMMddHHmmss
pay_order_no	M	String	64	平台订单号	21070211012001970631000383039
total_amount	M	long	12	订单金额，单位：分	200
counter_url	M	String	256	收银台地址信息	
响应样例
{
    "msg": "操作成功", 
    "resp_time": "20210922181057", 
    "code": "000000", 
    "resp_data": {
        "merchant_no": "8222900701106PZ", 
        "channel_id": "25", 
        "out_order_no": "KFPT20220714160009228907288", 
        "order_create_time": "20210922181056", 
        "order_efficient_time": "20210803141700", 
        "pay_order_no": "21092211012001970631000488056", 
        "counter_url": "http://q.huijingcai.top/b/pay?merchantNo=8221210594300JY&merchantOrderNo=08F4542EEC6A4497BC419161747A92FQ&payOrderNo=21092211012001970631000488056"
    }
}复制
返回码code一览表
msg	code
成功	000000

API文档

基础支付

聚合收银台

收银台订单查询
收银台订单查询
更新时间：2025-02-26 11:11:15
作者：wangyuwei
调用地址
使用HTTP协议，POST方式提交。

测试环境：https://test.wsmsd.cn/sit/api/v3/ccss/counter/order/query

生产环境：https://s2.lakala.com/api/v3/ccss/counter/order/query

请求参数
字段名	是否必输	类型	长度	字段描述	示例
out_order_no	C	String	32	商户订单号	12345678
merchant_no	M	String	32	银联商户号	822100041120005
pay_order_no	C	String	64	支付订单号	21070211012001970631000383039
channel_id	C	String	32	渠道号	10
说明：输入参数要么传out_order_no+merchant_no，要么传pay_order_no+merchant_no。

请求样例：

{ 
 "req_time": "20210922154316",  
 "version": "3.0",  
 "req_data": {    
   "pay_order_no": "21092211012001970631000488042",      
   "merchant_no": "822100041120005",      
   "channel_id": "15"
  }
}复制
响应参数
字段名	是否必输	类型	长度	字段描述	示例
pay_order_no	M	String	64	支付订单号	21070211012001970631000383039
out_order_no	M	String	32	商户订单号	12345678
channel_id	M	String	32	渠道号	
trans_merchant_no	C	String	32	交易商户号	
trans_term_no	C	String	16	交易终端号	
merchant_no	M	String	32	结算商户号（合单订单中该结算商户号为主单名义上结算商户号）	822126090640003
term_no	M	String	16	结算终端号（合单订单中该结算商户号为主单名义上结算终端号）	
order_status	M	String	2	订单状态	0:待支付 1:支付中 2:支付成功 3:支付失败 4:已过期 5:已取消 6:部分退款或者全部退款 7:订单已关闭枚举
order_info	C	String	100	订单描述	
total_amount	M	long	12	订单金额，单位：分	200
order_create_time	M	String	14	订单创建时间	格式yyyyMMddHHmmss
order_efficient_time	M	String	14	订单有效时间	格式yyyyMMddHHmmss
settle_type	C	String	4	结算类型（非合单） （“0”或者空，常规结算方式）	
split_mark	C	String	2	合单标识	“1”为合单，不填默认是为非拆单
counter_param	C	String	1024	json字符串 收银台参数	{\“pay_mode\“ : \“ALIPAY\“} ，指定支付方式为支付宝
counter_remark	C	String	128	收银台备注	
busi_type_param	C	String	256	业务类型控制参数，jsonStr格式	[{\“busi_type\“:\“UPCARD\“,\“params\“:{\“crd_flg\“:\“CRDFLG_D|CRDFLG_C|CRDFLG_OTH\“}},{\“busi_type\“:\“SCPAY\“,\“params\“:{\“crd_flg\“:\“CRDFLG_D\“}}]
说明：UPCARD-刷卡，SCPAY-扫码，CRDFLG_D-借记卡，CRDFLG_C-贷记卡，CRDFLG_OTH-不明确是借记卡还是贷记卡
说明：一旦使用该字段，则增加限制，必须在指定限制范围内支付。比如，只配置”busi_type”:”UPCARD”的参数而不配置”busi_type”:”SCPAY”的参数，则只能通过刷卡而不能通过扫码完成支付
out_split_info	C	List<>	
商户拆单信息,	详细字段见out_split_info字段说明
split_info	C	List<>	
交易拆单信息	详细字段见split_info字段说明
sgn_info	C	list<>	
签约协议号列表	[“1234”,”2345”]
goods_mark	C	String	2	商品标识	
goods_field	C	String	2048	商品信息	
order_trade_info_list	M	List<>	
订单交易信息列表	list单元为Object，Object对象包含如下字段 ，按交易完成时间逆序排列
–>trade_no	M	String	32	交易流水号	2021070266210002570007或者 21080302570007
–>log_No	M	String	14	对账单流水号	66210002570007或者 21080302570007
–>trade_ref_no	M	String	12	交易参考号	080302570007,仅busi_type为UPCARD时返回
–>trade_type	M	String	16	交易类型	PAY-消费 REFUND-退款 CANCEL-撤销
–>trade_status	M	String	2	支付状态	返回状态 S:成功 F:失败 C:被冲正 U:预记状态 X:发送失败 T: 发送超时 P: 处理中
–>trade_amount	M	long	12	交易金额，单位：分	200
–>payer_amount	M	long	12	付款人实际支付金额，单位：分	
–>user_id1	C	String	64	用户标识1	微信sub_open_id 支付宝buyer_logon_id（买家支付宝账号）
–>user_id2	C	String	64	用户标识2	微信openId 支付宝buyer_user_id 银联user_id
–>busi_type	M	String	16	支付业务类型：
UPCARD-银行卡
SCPAY-扫码支付
DCPAY-数币支付
ONLINE-线上支付	
–>trade_time	C	String	14	交易完时间	格式yyyyMMddHHmmss
–>acc_trade_no	C	String	32	付款受理交易流水号	支付宝流水号、微信流水号
–>payer_account_no	C	String	32	付款人账号	
–>payer_name	C	String	32	付款人名称（仅ONLINE交易返回）	
–>payer_account_bank	C	String	32	付款账号开户行	
–>acc_type	C	String	2	账户类型	busi_type为UPCARD时返回：00-借记卡,01-贷记卡,02-准贷记卡,03-预付卡
busi_type为SCPAY时返回：00：不确定,02-微信零钱,03-支付宝花呗,04-支付宝钱包,99-未知
–>pay_mode	C	String	2	付款方式	busi_type为SCPAY时返回：UQRCODEPAY-银联、WECHAT-微信、ALIPAY-支付宝
–>client_batch_no	C	String	6	终端批次号	刷卡交易终端批次号，只有busi_type为UPCARD时返回
–>client_seq_no	C	String	6	终端流水号	刷卡交易终端流水号，只有busi_type为UPCARD时返回
–>settle_merchant_no	C	String	32	结算商户号	
–>settle_term_no	C	String	16	结算终端号	
–>origin_trade_no	C	String	32	原交易流水号(扫码交易的退款场景中，对应原交易流水号)	2021070266210002570007
–>auth_code	C	String	64	快捷签约协议号	
–>bank_type	C	String	64	付款银行	
–>result_desc（待上线）	C	String	32	交易结果描述


out_split_info字段说明
字段名	中文名称	是否必填	类型	说明
out_sub_order_no	外部子订单号	M	String(32)	商户子订单号
merchant_no	商户号	M	String(32)	拉卡拉分配的银联商户号
term_no	终端号	M	String(32)	拉卡拉分配的业务终端号
amount	金额	M	String(12)	单位分，整数型字符
settle_type	结算类型（合单）	C	String(4)	“0”或者空，常规结算方式
split_info域信息
字段名	中文名称	是否必填	类型	说明
sub_trade_no	子单交易流水号	M	String(32)	子单交易流水号
sub_log_no	子单对账单流水号	M	String(14)	子单对账单流水号
out_sub_order_no	外部子订单号	M	String(32)	商户子订单号
merchant_no	商户号	M	String(32)	拉卡拉分配的银联商户号
term_no	终端号	M	String(32)	拉卡拉分配的业务终端号
amount	金额	M	String(12)	单位分，整数型字符
响应样例：

{
    "msg": "操作成功", 
    "resp_time": "20210922174806", 
    "code": "000000", 
    "resp_data": {
        "pay_order_no": "21092211012001970631000488042", 
        "out_order_no": "LABS1632300253YDMG", 
        "channel_id": "15", 
        "trans_merchant_no": "82216205947000G", 
        "trans_term_no": "D0060389", 
        "merchant_no": "82216205947000G", 
        "term_no": "D0060389", 
        "order_status": "2", 
        "order_info": "24865454154", 
        "total_amount": 3300, 
        "order_create_time": "20210922164413", 
        "order_efficient_time": "20221208165845", 
        "order_trade_info_list": [
            {
                "trade_no": "2021092251210203410010", 
                "log_No": "51210203410010", 
                "trade_type": "PAY", 
                "trade_status": "S", 
                "trade_amount": 3300, 
                "payer_amount": 0, 
                "user_id1": "", 
                "user_id2": "", 
                "busi_type": "ONLINE", 
                "trade_time": "2021092264452", 
                "acc_trade_no": "109221009853", 
                "payer_account_no": "", 
                "payer_name": "", 
                "payer_account_bank": "", 
                "acc_type": "99", 
                "pay_mode": "LKLAT"
            }
        ]
    }
}


收银台订单通知
更新时间：2025-07-16 11:36:51
作者：wanghuiling
调用地址
使用HTTP协议，POST方式提交。

由商户提供（交易通知地址：NOTIFY_URL），来源于订单系统通知过来的消息对象。

说明：通知接入方系统，通过延时队列进行散列通知，通知频率：间隔：1s/5s/5s/10s/3m/10m/20m/30m/1h/2h - 总计 4h3m21s。商户返回应答SUCCESS，将终止通知

请求参数
字段名	是否必输	类型	长度	字段描述	示例
pay_order_no	M	String	64	支付订单号	21070211012001970631000383039
out_order_no	M	String	32	商户订单号	12345678
channel_id	M	String	32	渠道号	
trans_merchant_no	C	String	32	交易商户号	
trans_term_no	C	String	16	交易终端号	
merchant_no	M	String	32	结算商户号	822126090640003
term_no	M	String	16	结算终端号	
order_status	M	String	2	订单状态	0:待支付 1:支付中 2:支付成功 3:支付失败 4:已过期 5:已取消 6：部分退款或者全部退款
order_info	C	String	100	订单描述	
total_amount	M	long	12	订单金额，单位：分	200
order_create_time	M	String	14	订单创建时间	格式yyyyMMddHHmmss
order_efficient_time	M	String	14	订单有效时间	格式yyyyMMddHHmmss
split_mark	C	String	2	合单标识	“1”为合单，不填默认是为非拆单
split_info	C	List<>	
交易拆单信息	详细字段见split_info字段说明
order_trade_info	M	Object	
订单交易信息,见以下	
–>trade_no	M	String	32	交易流水号	2021070266210002570007或者 21080302570007
–>log_no	M	String	14	对账单流水号	66210002570007或者 21080302570007
–>trade_ref_no	M	String	12	交易参考号	080302570007,仅busi_type为UPCARD时返回
–>trade_type	M	String	16	交易类型	PAY-消费 REFUND-退款 CANCEL-撤销
–>trade_status	M	String	2	支付状态	返回状态 S:成功 F:失败 C:被冲正 U:预记状态 X:发送失败 T: 发送超时 P: 处理中
–>trade_amount	M	long	12	交易金额，单位：分	200
–>payer_amount	M	long	12	付款人实际支付金额，单位：分	
–>user_id1	C	String	64	用户标识1	微信sub_open_id 支付宝buyer_logon_id（买家支付宝账号）
–>user_id2	C	String	64	用户标识2	微信openId 支付宝buyer_user_id 银联user_id
–>busi_type	M	String	16	支付业务类型：
UPCARD-银行卡
SCPAY-扫码支付
DCPAY-数币支付
ONLINE-线上支付ONLINE_WK-线上外卡
WK-外卡
ONLINE_B2B-线上系统网银B2B
ONLINE_UNION-线上系统银联收银台
ONLINE_B2C-线上系统网银B2C
ONLINE_QUICK-线上系统快捷
ONLINE_LKLAT-线上系统转账	
–>trade_time	C	String	14	交易完时间	格式yyyyMMddHHmmss
–>acc_trade_no	C	String	32	付款受理交易流水号	支付宝流水号、微信流水号
–>payer_account_no	C	String	32	付款人账号	
–>payer_name	C	String	32	付款人名称（仅ONLINE交易返回）	
–>payer_account_bank	C	String	32	付款账号开户行	
–>acc_type	C	String	2	账户类型	busi_type为UPCARD时返回：00-借记卡,01-贷记卡,02-准贷记卡,03-预付卡
busi_type为SCPAY时返回：02-微信零钱,03-支付宝花呗,04-支付宝钱包,99-未知
–>pay_mode	C	String	2	付款方式	busi_type为SCPAY时返回：UQRCODEPAY-银联、WECHAT-微信、ALIPAY-支付宝
–>client_batch_no	C	String	6	终端批次号	刷卡交易终端批次号，只有busi_type为UPCARD时返回
–>client_seq_no	C	String	6	终端流水号	刷卡交易终端流水号，只有busi_type为UPCARD时返回
–>settle_merchant_no	C	String	32	结算商户号	
–>settle_term_no	C	String	16	结算终端号	
–>origin_trade_no	C	String	32	原交易流水号(扫码交易的退款场景中，对应原交易流水号)	2021070266210002570007
–>trade_remark	C	String	64	交易备注	
–>auth_code	C	String	64	快捷签约协议号	
–>bank_type	C	String	64	付款银行	
–>acc_settle_amount	C	String	12	账户端结算金额	
–>acc_mdiscount_amount	C	String	12	商户侧优惠金额(账户端)	
–>acc_discount_amount	C	String	12	账户端优惠金额	
–>acc_other_discount_amount	C	String	12	账户端其它优惠金额	
–>request_ip	C
String
32	付款方IP	
counter_remark	C	String	128	 收银台备注	
split_info域信息
字段名	中文名称	是否必填	类型	说明
sub_trade_no	子单交易流水号	M	String(32)	子单交易流水号
sub_log_no	子单对账单流水号	M	String(14)	子单对账单流水号
out_sub_order_no	外部子交易流水号	M	String(32)	商户子交易流水号，商户号下唯一
merchant_no	商户号	M	String(32)	拉卡拉分配的银联商户号
term_no	终端号	M	String(32)	拉卡拉分配的业务终端号
amount	金额	M	String(12)	单位分，整数型字符
请求样例
{
    "channel_id": "10",
    "merchant_no": "82239105398007K",
    "order_create_time": "20220117112533",
    "order_efficient_time": "20220124112533",
    "order_status": "2",
    "order_trade_info": {
        "acc_trade_no": "2022011822001470651424354488",
        "acc_type": "00",
        "busi_type": "SCPAY",
        "log_no": "66212380030451",
        "pay_mode": "ALIPAY",
        "payer_amount": 1200,
        "settle_merchant_no": "82239105398007K",
        "settle_term_no": "C9597363",
        "trade_amount": 1200,
        "trade_no": "20220118110113230166212380030451",
        "trade_status": "S",
        "trade_time": "20220118170046",
        "trade_type": "PAY",
        "user_id1": "135******50",
        "user_id2": "2088312273770657"
    },
    "out_order_no": "3335ED2D29E04BB3B8D5AD696842B1BF",
    "pay_order_no": "22011711012001101011025385338",
    "split_info": [{
        "amount": "850",
        "merchant_no": "82239105398007K",
        "out_sub_order_no": "72FBA30FD4AB3A958C93CF72BDA21",
        "sub_log_no": "66212379982975",
        "sub_trade_no": "20220118110113230166212379982975",
        "term_no": "C9597363"
    },
    {
        "amount": "350",
        "merchant_no": "8223910541100CS",
        "out_sub_order_no": "D7BF24DE245CDBC16B76B7FB3E7C1",
        "sub_log_no": "66212380030458",
        "sub_trade_no": "20220118110113230166212380030458",
        "term_no": "D9486551"
    }],
    "split_mark": "1",
    "term_no": "C9597363",
    "total_amount": 67200,
    "trans_merchant_no": "82239105398007K",
    "trans_term_no": "D9587314"
}复制
响应报文
{
    "code": "SUCCESS", 
    "message": "执行成功"
}
