// utils/request.js
const app = getApp()

/**
 * 统一请求封装
 * @param {Object} options - 请求配置
 * @param {String} options.url - 请求路径（相对路径，会自动拼接 baseURL）
 * @param {String} options.method - 请求方法，默认 GET
 * @param {Object} options.data - 请求参数
 * @param {Boolean} options.needAuth - 是否需要token认证，默认true
 * @param {Boolean} options.showLoading - 是否显示加载提示，默认true
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    needAuth = true,
    showLoading = true
  } = options

  // 显示加载提示
  if (showLoading) {
    wx.showLoading({
      title: '加载中...',
      mask: true
    })
  }

  // 构造完整URL
  const baseURL = app.globalData.baseURL
  const fullUrl = `${baseURL}${url}`

  // 构造请求头
  const header = {
    'content-type': 'application/json'
  }

  // 添加token
  if (needAuth) {
    const token = app.globalData.token || wx.getStorageSync('token')
    if (token) {
      header.token = token
    } else {
      wx.hideLoading()
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      // 跳转登录页
      setTimeout(() => {
        wx.redirectTo({
          url: '/pages/login/login'
        })
      }, 1500)
      return Promise.reject({ msg: '未登录' })
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: fullUrl,
      method: method.toUpperCase(),
      data,
      header,
      success: (res) => {
        if (showLoading) {
          wx.hideLoading()
        }

        const { statusCode, data } = res

        // HTTP状态码检查
        if (statusCode !== 200) {
          wx.showToast({
            title: `请求失败 ${statusCode}`,
            icon: 'none'
          })
          reject(res)
          return
        }

        // 业务状态码检查
        if (data.code === 200) {
          resolve(data.data)
        } else if (data.code === 401) {
          // token过期或无效
          wx.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none'
          })
          app.clearUserInfo()
          setTimeout(() => {
            wx.redirectTo({
              url: '/pages/login/login'
            })
          }, 1500)
          reject(data)
        } else {
          // 其他业务错误
          wx.showToast({
            title: data.msg || '请求失败',
            icon: 'none'
          })
          reject(data)
        }
      },
      fail: (err) => {
        if (showLoading) {
          wx.hideLoading()
        }
        console.error('请求失败:', err)
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// GET请求
function get(url, data = {}, options = {}) {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  })
}

// POST请求
function post(url, data = {}, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

// PUT请求
function put(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

// DELETE请求
function del(url, data = {}, options = {}) {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

module.exports = {
  request,
  get,
  post,
  put,
  delete: del
}
