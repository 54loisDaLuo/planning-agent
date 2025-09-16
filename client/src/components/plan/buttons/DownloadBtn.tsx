import { downloadContent } from '@/api/baseApi';

interface DownloadBtnProps {
  title: string;
  outline: string;
  policy: string;
  format?: 'docx' | 'txt';
  downloadType?: 'outline' | 'full';
}

const DownloadBtn = ({
  title,
  outline,
  policy,
  format = 'docx',
  downloadType = 'outline',
}: DownloadBtnProps) => {
  const handleDownload = async () => {
    try {
      await downloadContent(title, outline, policy, format, downloadType);
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

    return (
    <button
      onClick={handleDownload}
      className="flex-shrink-0 border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 transition-colors min-w-[70px]"
    >
      {downloadType === 'outline' ? '下载大纲' : '下载全文'}
        </button>
  );
};

export default DownloadBtn;

// const DownloadBtn = () => {
//     return (
//         <button className="flex-shrink-0 border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 transition-colors min-w-[70px]">
//             下载
//         </button>
//     )
// };

// export default DownloadBtn;
