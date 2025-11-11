import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // depts
  getDepts: (params = {}) => request.get('/dept/list', { params }),
  createDept: (data = {}) => request.post('/dept/create', data),
  updateDept: (data = {}) => request.post('/dept/update', data),
  deleteDept: (params = {}) => request.delete('/dept/delete', { params }),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),

  // wechat mini program
  getWechatList: (params = {}) => request.get('/wechat/list', { params }),
  getWechatById: (params = {}) => request.get('/wechat/get', { params }),
  createWechat: (data = {}) => request.post('/wechat/create', data),
  updateWechat: (data = {}) => request.post('/wechat/update', data),
  deleteWechat: (params = {}) => request.delete('/wechat/delete', { params }),
  updateWechatLogo: (data = {}) => request.post('/wechat/update_logo', data),
  updateWechatQrcode: (data = {}) => request.post('/wechat/update_qrcode', data),
  updateWechatStatus: (data = {}) => request.post('/wechat/update_status', data),
  uploadWechatFile: (formData) => request.post('/wechat/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  restoreWechat: (data = {}) => request.post('/wechat/restore', data),

  // crawler management
  getCrawlerTasks: (params = {}) => request.get('/crawler/task/list', { params }),
  createCrawlerTask: (data = {}) => request.post('/crawler/task/create', data),
  startCrawlerTask: (data = {}) => request.post('/crawler/task/start', data),
  stopCrawlerTask: (data = {}) => request.post('/crawler/task/stop', data),
  getCrawlerTaskStatus: (params = {}) => request.get('/crawler/task/status', { params }),
  updateCrawlerTask: (data = {}) => request.post('/crawler/task/update', data),
  syncOdsToWechat: (data = {}) => request.post('/crawler/ods/sync_to_wechat', data),
}
