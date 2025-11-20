// pages/login/login.js
const api = require('../../api/index')
const app = getApp()

Page({
  data: {
    loading: false,
    useMock: false // 切换为真实接口模式
  },

  onLoad(options) {
    console.log('登录页加载', options)
    // 检查是否已登录
    if (app.checkLogin()) {
      wx.switchTab({
        url: '/pages/home/home'
      })
    }
  },

  /**
   * 处理登录
   */
  handleLogin() {
    this.setData({ loading: true })

    // Mock 模式：直接模拟登录成功
    if (this.data.useMock) {
      this.mockLogin()
      return
    }

    // 获取用户头像/昵称后再登录
    wx.getUserProfile({
      desc: '用于完善资料',
      success: (profileRes) => {
        const { nickName, avatarUrl } = profileRes.userInfo || {}
        // 真实登录流程
        wx.login({
          success: (res) => {
            if (res.code) {
              this.doLogin(res.code, nickName || '', avatarUrl || '')
            } else {
              console.error('获取 code 失败', res)
              wx.showToast({
                title: '登录失败',
                icon: 'none'
              })
              this.setData({ loading: false })
            }
          },
          fail: (err) => {
            console.error('wx.login 失败', err)
            wx.showToast({
              title: '登录失败',
              icon: 'none'
            })
            this.setData({ loading: false })
          }
        })
      },
      fail: () => {
        // 用户拒绝授权，也允许匿名登录
        wx.login({
          success: (res) => {
            if (res.code) {
              this.doLogin(res.code, '', '')
            } else {
              wx.showToast({ title: '登录失败', icon: 'none' })
              this.setData({ loading: false })
            }
          },
          fail: () => {
            wx.showToast({ title: '登录失败', icon: 'none' })
            this.setData({ loading: false })
          }
        })
      }
    })
  },

  /**
   * 调用后端登录接口
   */
  doLogin(code, nickname = '', avatarUrl = '') {
    api.login(code, nickname, avatarUrl)
      .then((data) => {
        console.log('登录成功', data)
        
        // 保存 token 和用户信息（使用后端返回的 user）
        const { access_token, user } = data
        app.setUserInfo(user || {}, access_token)
        
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        })

        // 跳转首页
        setTimeout(() => {
          wx.switchTab({
            url: '/pages/home/home'
          })
        }, 500)
      })
      .catch((err) => {
        console.error('登录失败', err)
        wx.showToast({
          title: err.msg || '登录失败',
          icon: 'none'
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  /**
   * Mock 登录（开发测试用）
   */
  mockLogin() {
    console.log('使用 Mock 登录')
    
    setTimeout(() => {
      // 模拟返回的数据
      const mockData = {
        access_token: 'mock_token_' + Date.now(),
        username: 'wx_mock_user'
      }

      // 保存到本地和全局
      app.setUserInfo(
        { username: mockData.username },
        mockData.access_token
      )

      wx.showToast({
        title: 'Mock 登录成功',
        icon: 'success'
      })

      // 跳转首页
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/home/home'
        })
      }, 1500)

      this.setData({ loading: false })
    }, 1000)
  }
})
