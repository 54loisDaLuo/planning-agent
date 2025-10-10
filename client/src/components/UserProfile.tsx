'use client';

import React, { useState } from 'react';

interface UserProfileProps {
  username: string;
}
const UserProfile: React.FC<UserProfileProps> = ({ username }) => {
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword !== confirmPassword) {
      setError('新密码和确认密码不一致');
      return;
    }

    if (newPassword.length < 6) {
      setError('新密码长度至少6位');
      return;
    }

    setLoading(true);

    try {
      // 获取当前用户ID（需要从localStorage或其他地方获取）
      const userData = localStorage.getItem('user');
      if (!userData) {
        setError('用户信息不存在，请重新登录');
        return;
      }

      const user = JSON.parse(userData);

      // 修改：使用后端API需要的参数格式
      const params = new URLSearchParams();
      params.append('user_id', user.id.toString());
      params.append('new_password', newPassword);

      const response = await fetch(
        `http://localhost:8000/api/user/change-password?${params.toString()}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      if (response.ok) {
        setNewPassword('');
        setConfirmPassword('');
        setSuccess('密码修改成功');
        setShowChangePassword(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '密码修改失败');
      }
    } catch (err) {
      setError('网络错误，请检查服务器连接');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">用户信息</h3>
      <p className="text-gray-600">用户名: {username}</p>

      <button
        onClick={() => setShowChangePassword(!showChangePassword)}
        className="mt-4 text-indigo-600 hover:text-indigo-900"
      >
        {showChangePassword ? '取消修改' : '修改密码'}
      </button>

      {showChangePassword && (
        <form onSubmit={handleChangePassword} className="mt-4 space-y-4">
          {/* 移除原密码输入框 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              新密码
            </label>
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="请输入新密码"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              确认新密码
            </label>
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="请再次输入新密码"
            />
          </div>

          {error && <div className="text-red-600 text-sm">{error}</div>}
          {success && <div className="text-green-600 text-sm">{success}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? '修改中...' : '确认修改'}
          </button>
        </form>
      )}
    </div>
  );
};

export default UserProfile;
