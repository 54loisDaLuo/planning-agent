'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 修复：使用查询参数格式而不是表单数据格式
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await fetch(
        `http://localhost:8000/api/user/login?${params.toString()}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        // 根据后端实际返回的数据结构调整
        localStorage.setItem('token', 'authenticated'); // 后端没有返回token，使用固定值
        localStorage.setItem('user', JSON.stringify({ id: data.user_id }));
        router.push('/');
      } else {
        // 修复错误处理逻辑
        let errorMessage = '登录失败';

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
          errorMessage = response.statusText || '登录失败';
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {/* 增加容器宽度，确保标题有足够空间 */}
      <div className="max-w-lg w-full space-y-8">
        {/* 标题区域 - 放在最前面 */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-indigo-600 whitespace-nowrap">
            智策云笔·基于知识库的报告撰写与实时问答平台
          </h1>
        </div>

        <div>
          <h2 className="mt-6 text-center text-xl font-extrabold text-gray-900">
            用户登录
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? '登录中...' : '登录'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">测试账号: admin / admin123</p>
          </div>
        </form>
      </div>
    </div>
  );
}
