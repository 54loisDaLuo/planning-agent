'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: number;
  username: string;
  password: string;
}

// 新增：修改密码模态框组件
interface ChangePasswordModalProps {
  user: User;
  isOpen: boolean;
  onClose: () => void;
  onPasswordChange: () => void;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  user,
  isOpen,
  onClose,
  onPasswordChange,
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

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
        onPasswordChange();
        onClose();
        alert('密码修改成功');
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">
          修改密码 - {user.username}
        </h3>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
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
          </div>

          {error && <div className="mt-4 text-red-600 text-sm">{error}</div>}

          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? '修改中...' : '确认修改'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // 新增：修改密码模态框状态
  const [changePasswordModal, setChangePasswordModal] = useState<{
    isOpen: boolean;
    user: User | null;
  }>({
    isOpen: false,
    user: null,
  });

  // 新增：修改密码处理函数
  const handleChangePassword = (user: User) => {
    setChangePasswordModal({
      isOpen: true,
      user,
    });
  };

  const handleCloseModal = () => {
    setChangePasswordModal({
      isOpen: false,
      user: null,
    });
  };

  const handlePasswordChangeSuccess = () => {
    fetchUsers(); // 刷新用户列表
  };
  const router = useRouter();

  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchUsers();
  }, [router]);

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/user/query');
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (err) {
      setError('获取用户列表失败');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 修复：使用查询参数格式
      const params = new URLSearchParams();
      params.append('username', newUsername);
      params.append('password', newPassword);

      const response = await fetch(
        `http://localhost:8000/api/user/create?${params.toString()}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      if (response.ok) {
        setNewUsername('');
        setNewPassword('');
        fetchUsers();
      } else {
        // 修复错误处理逻辑
        let errorMessage = '创建用户失败';

        try {
          const errorData = await response.json();
          console.log('后端返回的错误数据:', errorData); // 调试信息

          // 检查不同的错误响应格式
          if (errorData.detail) {
            // 处理数组格式的验证错误
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail
                .map((err) => String(err.msg || err.message || '验证错误'))
                .join(', ');
            } else {
              errorMessage = String(errorData.detail);
            }
          } else if (errorData.message) {
            errorMessage = String(errorData.message);
          } else if (typeof errorData === 'string') {
            errorMessage = errorData;
          } else if (errorData.error) {
            errorMessage = String(errorData.error);
          } else if (Array.isArray(errorData)) {
            // 处理数组格式的错误
            errorMessage = errorData
              .map((err) => String(err.msg || err.message || err))
              .join(', ');
          } else if (typeof errorData === 'object') {
            // 如果是对象但不是预期的格式，转换为字符串
            errorMessage = JSON.stringify(errorData);
          }
        } catch (jsonError) {
          // 如果JSON解析失败，使用状态文本
          console.log('JSON解析错误:', jsonError);
          errorMessage = response.statusText || '创建用户失败';
        }

        console.log('最终错误消息:', errorMessage); // 调试信息
        setError(String(errorMessage)); // 确保是字符串
      }
    } catch (err) {
      // 修复网络错误处理
      console.log('网络错误:', err);
      const errorMessage =
        err instanceof Error ? err.message : '网络错误，请检查服务器连接';
      setError(String(errorMessage)); // 确保是字符串
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('确定要删除这个用户吗？')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/user/${userId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchUsers();
      } else {
        setError('删除用户失败');
      }
    } catch (err) {
      setError('网络错误');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            {/* 添加首页按钮和标题区域 */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">用户管理</h2>
              <button
                onClick={() => router.push('/')}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
              >
                返回首页
              </button>
            </div>

            {/* 创建用户表单 */}
            <form onSubmit={handleCreateUser} className="mb-8">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="用户名"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                  />
                </div>
                <div>
                  <input
                    type="password"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="密码"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {loading ? '创建中...' : '创建用户'}
                  </button>
                </div>
              </div>
            </form>

            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            )}

            {/* 用户列表 */}
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      用户名
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      密码
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {user.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {user.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {user.password}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {/* 新增：修改密码按钮 */}
                        <button
                          onClick={() => handleChangePassword(user)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          修改密码
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>{' '}
          {/* 修复：添加缺失的闭合div标签 */}
        </div>{' '}
        {/* 修复：添加缺失的闭合div标签 */}
        {/* 新增：修改密码模态框 */}
        {changePasswordModal.user && (
          <ChangePasswordModal
            user={changePasswordModal.user}
            isOpen={changePasswordModal.isOpen}
            onClose={handleCloseModal}
            onPasswordChange={handlePasswordChangeSuccess}
          />
        )}
      </div>
    </div>
  );
}
