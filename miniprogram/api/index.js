// api/index.js
const { get, post } = require('../utils/request')

/**
 * 小程序登录
 * @param {String} code - wx.login 返回的 code
 * @param {String} nickname - 用户昵称（可选）
 * @param {String} avatarUrl - 用户头像（可选）
 */
function login(code, nickname = '', avatarUrl = '') {
  return post('/wxapp/auth/login', {
    code,
    nickname,
    avatarUrl
  }, {
    needAuth: false // 登录接口不需要token
  })
}

/**
 * 获取用户信息
 */
function getUserProfile() {
  return get('/wxapp/auth/profile')
}

/**
 * 获取首页数据
 * @param {Object} params - 查询参数
 */
function getHome(params = {}) {
  return get('/wxapp/home', params, {
    needAuth: false // 首页可以未登录访问
  })
}

/**
 * 获取小程序列表
 * @param {Object} params - 查询参数
 */
function getAppList(params = {}) {
  return get('/wxapp/list', params, {
    needAuth: false
  })
}

/**
 * 获取小程序详情
 * @param {Number} id - 小程序ID
 */
function getAppDetail(id) {
  return get(`/wxapp/detail/${id}`, {}, {
    needAuth: false
  })
}

/**
 * 获取分类列表
 */
function getCategories() {
  return get('/wxapp/categories', {}, {
    needAuth: false
  })
}

/**
 * 获取我的收藏列表
 * @param {Object} params - 分页参数
 */
function getFavoriteList(params = {}) {
  return get('/wxapp/favorite/list', params)
}

/**
 * 收藏/取消收藏
 * @param {Number} app_id - 小程序ID
 * @param {Boolean} value - true=收藏, false=取消
 */
function toggleFavorite(app_id, value) {
  return post('/wxapp/favorite/toggle', {
    app_id,
    value
  })
}

/**
 * 设为常用/取消常用
 * @param {Number} app_id - 小程序ID
 * @param {Boolean} value - true=设为常用, false=取消
 */
function pinFavorite(app_id, value) {
  return post('/wxapp/favorite/pin', {
    app_id,
    value
  })
}

/**
 * 埋点事件上报
 * @param {String} event - 事件名称
 * @param {Object} payload - 事件数据
 */
function trackEvent(event, payload = {}) {
  return post('/wxapp/track/event', {
    event,
    payload
  })
}

module.exports = {
  login,
  getUserProfile,
  getHome,
  getAppList,
  getAppDetail,
  getCategories,
  getFavoriteList,
  toggleFavorite,
  pinFavorite,
  trackEvent
}
