'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Hero from '@/sections/hero';

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsLoggedIn(false);
    router.push('/login');
  };

  return (
    <>
      <div className="absolute top-4 right-4 space-x-4">
        {isLoggedIn ? (
          <>
            <button
              onClick={() => router.push('/admin/users')}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              用户管理
            </button>
            <button
              onClick={handleLogout}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
            >
              退出登录
            </button>
          </>
        ) : (
          <button
            onClick={() => router.push('/login')}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            登录
          </button>
        )}
      </div>
      <Hero />
    </>
  );
}
