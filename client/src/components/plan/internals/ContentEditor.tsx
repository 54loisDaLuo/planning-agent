// "use client";

// import React, { useState, useEffect } from "react";
// import { GenerateContentResponse } from "@/data/generateTypes";
// import EditableContent from "./EditableContent";
// import RewriteInput from "../RewriteInput";
// import { rewriteContentParagraph } from "@/api/generateApi";

// interface ContentEditorProps {
//     initialContentData: GenerateContentResponse['content'];
//     planTitle: string;
//     policyContext: string;
// }

// type RewriteTarget = {
//     sectionIndex: number;
//     childIndex: number;
// } | null;

// const ContentEditor = ({ initialContentData, planTitle, policyContext }: ContentEditorProps) => {
//     // 内部状态，用于管理和编辑内容
//     const [content, setContent] = useState(initialContentData);
//     const [rewriteTarget, setRewriteTarget] = useState<RewriteTarget>(null);
//     const [isLoading, setIsLoading] = useState(false);

//     // 核心修复：使用 useEffect 同步外部传入的数据
//     // 当 initialContentData 这个 prop 发生变化时（例如，在父组件中重写了全部内容），
//     // 这个 effect 会被触发，从而更新组件的内部状态 content。
//     useEffect(() => {
//         setContent(initialContentData);
//     }, [initialContentData]);

// const handleRewriteSubmit = async (user_requirement: string) => {
//     if (!rewriteTarget) return;
//     setIsLoading(true);

//     const { sectionIndex, childIndex } = rewriteTarget;
//     const section = content.content_outline[sectionIndex];
//     const child = section.children?.[childIndex];

//     if (!child) {
//         setIsLoading(false);
//         return;
//     }

//     try {
//         const res = await rewriteContentParagraph(
//             planTitle,
//             section.title,
//             child.title,
//             child.content || "",
//             policyContext,
//             user_requirement
//         );

//         if (res && res.success) {
//             const newContentOutline = JSON.parse(JSON.stringify(content.content_outline));
//             newContentOutline[sectionIndex].children[childIndex].content = res.new_content;
//             setContent({ ...content, content_outline: newContentOutline });
//         }
//     } catch (error) {
//         console.error("重写内容失败:", error);
//         alert("重写内容失败，请检查网络或联系管理员。");
//     } finally {
//         setIsLoading(false);
//         setRewriteTarget(null);
//     }
// };

//     return (
//         <div className="space-y-8 py-4">
//             {content.content_outline.map((section, i) => (
//                 <div key={i} className="space-y-4">
//                     <h2 className="text-xl font-bold text-gray-900 border-b pb-2">
//                         {section.title}
//                     </h2>

//                     {section.children?.map((child, j) => (
//                         <div key={j} className="ml-4 space-y-2">
//                             <h3 className="text-lg font-semibold text-gray-800">
//                                 {child.title}
//                             </h3>

//                             {rewriteTarget && rewriteTarget.sectionIndex === i && rewriteTarget.childIndex === j && (
//                                 <div className="mb-2">
//                                     <RewriteInput
//                                         isLoading={isLoading}
//                                         onSubmit={handleRewriteSubmit}
//                                         onClose={() => setRewriteTarget(null)}
//                                     />
//                                 </div>
//                             )}

//                             <EditableContent
//                                 defaultValue={child.content || ""}
//                                 onRewriteClick={() => setRewriteTarget({ sectionIndex: i, childIndex: j })}
//                             />
//                         </div>
//                     ))}
//                 </div>
//             ))}
//         </div>
//     );
// };

// export default ContentEditor;

'use client';

import React, { useState, useEffect } from 'react';
import { GenerateContentResponse } from '@/data/generateTypes';
import EditableContent from './EditableContent';
import RewriteInput from '../RewriteInput';
import { rewriteContentParagraph, webSearchParagraph } from '@/api/generateApi';
import WebSearchConfirmModal from '../WebSearchConfirmModal';

interface ContentEditorProps {
  initialContentData: GenerateContentResponse['content'];
  planTitle: string;
  policyContext: string;
  onWebSearchResults?: (
    results: Array<{
      url: string;
      title: string;
      content: string;
      score: number;
    }>
  ) => void;
}

type RewriteTarget = {
  sectionIndex: number;
  childIndex: number;
  userRequirement: string; // 添加用户需求字段
} | null;

type CurrentRewriteTarget = {
  sectionTitle: string;
  subtitleTitle: string;
  currentContent: string;
} | null;

const ContentEditor = ({
  initialContentData,
  planTitle,
  policyContext,
  onWebSearchResults,
}: ContentEditorProps) => {
  const [content, setContent] = useState(initialContentData);
  const [rewriteTarget, setRewriteTarget] = useState<RewriteTarget>(null);
  const [currentRewriteTarget, setCurrentRewriteTarget] =
    useState<CurrentRewriteTarget>(null);
  const [showWebSearchConfirm, setShowWebSearchConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setContent(initialContentData);
  }, [initialContentData]);

  const handleRewriteSubmit = async (user_requirement: string) => {
    // alert('handleRewriteSubmit被调用');
    // alert('用户需求: ' + user_requirement);
    // alert('sectionIndex: ' + rewriteTarget?.sectionIndex);
    // alert('childIndex: ' + rewriteTarget?.childIndex);

    if (!rewriteTarget) return;
    setIsLoading(true);

    const { sectionIndex, childIndex } = rewriteTarget;
    const section = content.content_outline[sectionIndex];
    const child = section.children?.[childIndex];

    if (!child) {
      setIsLoading(false);
      return;
    }

    try {
      // 设置当前重写目标用于联网搜索
      setCurrentRewriteTarget({
        sectionTitle: section.title,
        subtitleTitle: child.title,
        currentContent: child.content || '',
      });

      // 同时设置rewriteTarget包含用户需求
      setRewriteTarget({
        sectionIndex,
        childIndex,
        userRequirement: user_requirement, // 保存用户需求
      });

      // 显示联网搜索确认弹窗
      setShowWebSearchConfirm(true);
    } catch (error) {
      console.error('重写内容失败:', error);
      alert('重写内容失败，请检查网络或联系管理员。');
    } finally {
      setIsLoading(false);
      // 移除 setRewriteTarget(null); 这行
    }
  };

  // 联网搜索确认处理
  const handleWebSearchConfirm = async (enableWebSearch: boolean) => {
    setShowWebSearchConfirm(false);
    if (!currentRewriteTarget || !rewriteTarget) return;

    const { sectionTitle, subtitleTitle, currentContent } =
      currentRewriteTarget;
    const { sectionIndex, childIndex } = rewriteTarget;

    try {
      // 实际调用API进行内容重写
      const rewriteResult = await rewriteContentParagraph(
        planTitle,
        sectionTitle,
        subtitleTitle,
        currentContent,
        policyContext,
        rewriteTarget?.userRequirement || '' // 使用正确的变量
      );

      // 如果启用联网搜索，调用联网搜索API
      if (enableWebSearch) {
        const webSearchResult = await webSearchParagraph(
          planTitle,
          sectionTitle,
          subtitleTitle
        );

        // 如果有联网搜索结果回调函数，调用它
        if (onWebSearchResults && webSearchResult.web_search_infos) {
          onWebSearchResults(webSearchResult.web_search_infos);
        }
      }

      // 更新内容
      if (rewriteResult.success && rewriteResult.new_content) {
        setContent((prevContent) => {
          const newContent = { ...prevContent };
          newContent.content_outline[sectionIndex].children[
            childIndex
          ].content = rewriteResult.new_content;
          return newContent;
        });
      }
    } catch (error) {
      console.error('重写失败:', error);
      alert('重写失败，请检查网络或联系管理员。');
    } finally {
      setCurrentRewriteTarget(null);
      setRewriteTarget(null); // 在这里设置rewriteTarget为null
    }
  };

  return (
    <div className="space-y-8 py-4">
      {content.content_outline.map((section, i) => (
        <div key={i} className="space-y-4">
          <h2 className="text-xl font-bold text-gray-900 border-b pb-2">
            {section.title}
          </h2>

          {section.children?.map((child, j) => (
            <div key={j} className="ml-4 space-y-2">
              <h3 className="text-lg font-semibold text-gray-800">
                {child.title}
              </h3>

              {rewriteTarget &&
                rewriteTarget.sectionIndex === i &&
                rewriteTarget.childIndex === j && (
                  <div className="mb-2">
                    <RewriteInput
                      isLoading={isLoading}
                      onSubmit={handleRewriteSubmit}
                      onClose={() => setRewriteTarget(null)}
                    />
                  </div>
                )}

              <EditableContent
                defaultValue={child.content || ''}
                onRewriteClick={() =>
                  setRewriteTarget({ sectionIndex: i, childIndex: j })
                }
              />
            </div>
          ))}
        </div>
      ))}

      <WebSearchConfirmModal
        isOpen={showWebSearchConfirm}
        onConfirm={handleWebSearchConfirm}
        onClose={() => {
          setShowWebSearchConfirm(false);
          setCurrentRewriteTarget(null);
          setRewriteTarget(null);
        }}
      />
    </div>
  );
};

export default ContentEditor;
