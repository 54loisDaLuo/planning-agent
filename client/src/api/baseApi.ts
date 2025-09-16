const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const fetchKbList = async () => {
    const res = await fetch(`${API_BASE_URL}/api/kb/list`);
  if (!res.ok) throw new Error('(from baseApi.ts)知识库列表获取失败');
    return await res.json();
};

export const uploadKnowledgeBase = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/api/kb/upload`, {
        method: 'POST',
    body: formData,
    });
    if (!res.ok) throw new Error('(from baseApi.ts)知识库文件上传失败');
    return await res.json();
};

export const deleteKnowledgeBase = async (filename: string) => {
    const res = await fetch(`${API_BASE_URL}/api/kb/delete`, {
        method: 'POST',
        headers: {
      'Content-Type': 'application/json',
        },
    body: JSON.stringify({ filename }),
    });
    if (!res.ok) throw new Error('(from baseApi.ts)知识库文件删除失败');
    return await res.json();
};

// 下载大纲
export const downloadOutline = async (
  title: string,
  outline: string,
  policy: string,
  format: string = 'docx'
) => {
  const response = await fetch(`${API_BASE_URL}/api/kb/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, outline, policy, format }),
  });

  if (!response.ok) {
    throw new Error('下载失败');
  }

  // 处理文件下载
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = `${title}.${format}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

// 下载全文
export const downloadContent = async (
  title: string,
  outline: string,
  policy: string,
  format: 'docx' | 'txt' = 'docx',
  downloadType: 'outline' | 'full' = 'outline'
): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/kb/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title,
      outline,
      policy,
      format,
      download_type: downloadType,
    }),
  });

  if (!response.ok) {
    throw new Error('下载失败');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title}_${downloadType}.${format}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
