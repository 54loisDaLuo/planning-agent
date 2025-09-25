// const RightContent = () => (
//   <div className="flex flex-col h-full min-h-0">
//     <div className="flex-1 min-h-0">
//       <div className="text-center mb-6">
//         <h3 className="text-lg font-semibold text-blue-600">实时问答</h3>
//       </div>
//       <div className="bg-gray-50 rounded-lg p-4 mb-4 overflow-y-auto min-h-32 h-full">
//         <div className="text-gray-500 text-sm text-center">
//           随时输入您想问的问题，包括查询资料、联系协调等......
//         </div>
//       </div>
//     </div>
//     <form className="mt-auto flex flex-wrap gap-2">
//       <input
//         type="text"
//         placeholder="输入您的问题..."
//         className="flex-1 min-w-[120px] border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
//       />
//       <button
//         type="submit"
//         className="flex-shrink-0 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors min-w-[60px]"
//       >
//         发送
//       </button>
//     </form>
//   </div>
// );

// export default RightContent;

// interface RightContentProps {
//   webSearchResults?: Array<{
//     url: string;
//     title: string;
//     content: string;
//     score: number;
//   }>;
// }

// const RightContent = ({ webSearchResults = [] }: RightContentProps) => (
//   <div className="flex flex-col h-full min-h-0">
//     <div className="flex-1 min-h-0">
//       <div className="text-center mb-6">
//         <h3 className="text-lg font-semibold text-blue-600">实时问答</h3>
//       </div>
//       <div className="bg-gray-50 rounded-lg p-4 mb-4 overflow-y-auto min-h-32 h-full">
//         {webSearchResults.length > 0 ? (
//           <div className="space-y-3">
//             <h4 className="font-medium text-gray-700">联网搜索结果：</h4>
//             {webSearchResults.map((result, index) => (
//               <div key={index} className="bg-white p-3 rounded border">
//                 <a
//                   href={result.url}
//                   target="_blank"
//                   rel="noopener noreferrer"
//                   className="text-blue-600 hover:underline font-medium"
//                 >
//                   {result.title}
//                 </a>
//                 <p className="text-sm text-gray-600 mt-1">
//                   {result.content.length > 200
//                     ? `${result.content.substring(0, 200)}...`
//                     : result.content}
//                 </p>
//                 <div className="text-xs text-gray-500 mt-1">
//                   相关度: {result.score}
//                 </div>
//               </div>
//             ))}
//           </div>
//         ) : (
//           <div className="text-gray-500 text-sm text-center">
//             随时输入您想问的问题，包括查询资料、联系协调等......
//           </div>
//         )}
//       </div>
//     </div>
//     <form className="mt-auto flex flex-wrap gap-2">
//       <input
//         type="text"
//         placeholder="输入您的问题..."
//         className="flex-1 min-w-[120px] border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
//       />
//       <button
//         type="submit"
//         className="flex-shrink-0 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors min-w-[60px]"
//       >
//         发送
//       </button>
//     </form>
//   </div>
// );

// export default RightContent;

interface RightContentProps {
  webSearchResults?: Array<{
    url: string;
    title: string;
    content: string;
    score: number;
  }>;
}

const RightContent = ({ webSearchResults = [] }: RightContentProps) => (
  <div className="flex flex-col h-full min-h-0">
    {/* 实时问答标题 - 固定位置 */}
    <div className="text-center mb-4 flex-shrink-0">
      <h3 className="text-lg font-semibold text-blue-600">实时问答</h3>
    </div>

    {/* 主要内容区域 - 可滚动 */}
    <div className="flex-1 min-h-0 overflow-hidden">
      {/* 联网搜索结果区域 - 可滚动，固定最大高度 */}
      {webSearchResults.length > 0 && (
        <div className="mb-4 flex-shrink-0">
          <h4 className="font-medium text-gray-700 mb-2">联网搜索结果：</h4>
          <div className="bg-gray-50 rounded-lg p-3 overflow-y-auto max-h-110 ">
            <div className="space-y-2">
              {webSearchResults.map((result, index) => (
                <div
                  key={index}
                  className="bg-white p-2 rounded border text-sm"
                >
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline font-medium block"
                  >
                    {result.title}
                  </a>
                  <p className="text-gray-600 mt-1">
                    {result.content.length > 120
                      ? `${result.content.substring(0, 120)}...`
                      : result.content}
                  </p>
                  <div className="text-xs text-gray-500 mt-1">
                    相关度: {result.score}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 问答内容区域 - 可伸缩 */}
      <div className="bg-gray-50 rounded-lg p-4 h-full overflow-y-auto">
        {webSearchResults.length === 0 ? (
          <div className="text-gray-500 text-sm text-center h-full flex items-center justify-center">
            随时输入您想问的问题，包括查询资料、联系协调等......
          </div>
        ) : (
          <div className="text-gray-500 text-sm text-center h-full flex items-center justify-center">
            请输入您的问题进行实时问答
          </div>
        )}
      </div>
    </div>

    {/* 输入框区域 - 固定在底部，固定宽度，不被遮挡 */}
    <div className="mt-auto flex-shrink-0 pt-4 border-gray-200">
      <form className="flex gap-2 w-full">
        <input
          type="text"
          placeholder="输入您的问题..."
          className="flex-1 min-w-0 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          className="flex-shrink-0 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors min-w-[60px]"
        >
          发送
        </button>
      </form>
    </div>
  </div>
);

export default RightContent;
