import React, { useState, useEffect } from 'react';
import { OutlineStruct, OutlineSection } from '@/data/contentTypes';
import EditableTitle from './EditableTitle';
import { GenerateOutlineResponse } from '@/data/generateTypes';

interface OutlineEditorProps {
  // We now expect the full initial data object
  initialData: GenerateOutlineResponse;
  onOutlineUpdate?: (outline: OutlineStruct) => void;
}

// 辅助函数：检查字符串是否为有效的JSON
const isValidJSON = (str: string): boolean => {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
};

// 辅助函数：安全解析JSON，如果无效则返回空数组
const safeJSONParse = (str: string): OutlineStruct => {
  try {
    const parsed = JSON.parse(str);
    // 验证解析结果是否为有效的OutlineStruct格式
    if (
      Array.isArray(parsed) &&
      parsed.every(
        (section) =>
          typeof section === 'object' && section !== null && 'title' in section
      )
    ) {
      return parsed;
    }
    return [];
  } catch {
    return [];
  }
};

const OutlineEditor = ({
  initialData,
  onOutlineUpdate,
}: OutlineEditorProps) => {
  // const OutlineEditor = ({ initialData }: OutlineEditorProps) => {
  // The outline data is now managed as state within this component
  const [outline, setOutline] = useState<OutlineStruct>([]);
  const [lastValidOutline, setLastValidOutline] = useState<OutlineStruct>([]);

  // When the initialData from the parent changes, update the state
  // When the initialData from the parent changes, update the state
  useEffect(() => {
    try {
      let parsedOutline: OutlineStruct;

      if (typeof initialData.outline === 'string') {
        // 如果是字符串，检查是否为有效JSON
        if (isValidJSON(initialData.outline)) {
          parsedOutline = safeJSONParse(initialData.outline);
          setLastValidOutline(parsedOutline); // 保存最后一个有效的大纲
        } else {
          // 如果JSON无效，使用最后一个有效的大纲
          parsedOutline = lastValidOutline;
          console.debug('JSON数据不完整，使用最后一个有效的大纲');
        }
      } else {
        // 如果不是字符串，直接使用
        parsedOutline = initialData.outline;
        setLastValidOutline(parsedOutline); // 保存最后一个有效的大纲
      }

      setOutline(parsedOutline);
    } catch (error) {
      console.debug('大纲数据解析失败，使用最后一个有效的大纲:', error);
      setOutline(lastValidOutline);
    }
  }, [initialData.outline]); // 移除 lastValidOutline 依赖

  // 在OutlineEditor.tsx中添加回调函数
  const handleOutlineChange = (newOutline: OutlineStruct) => {
    setOutline(newOutline);
    setLastValidOutline(newOutline); // 更新最后一个有效的大纲
    // 添加这行，将更新后的大纲同步到父组件
    onOutlineUpdate?.(newOutline);
  };

  return (
    <div className="space-y-6 font-medium">
      {outline.length > 0 ? (
        outline.map((section, i) => (
          <div key={i} className="space-y-3">
            {/* Pass all necessary context and the change handler to the main title */}
            <EditableTitle
              defaultValue={section.title}
              isSub={false}
              fullOutline={outline}
              sectionIndex={i}
              onOutlineChange={handleOutlineChange}
              planTitle={initialData.title}
              policyContext={initialData.policy}
            />
            {/* Pass all necessary context and the change handler to each subtitle */}
            {section.children?.map((child, j) => (
              <div key={j} className="ml-8">
                <EditableTitle
                  defaultValue={child.title}
                  isSub={true}
                  fullOutline={outline}
                  sectionIndex={i}
                  childIndex={j}
                  onOutlineChange={handleOutlineChange}
                  planTitle={initialData.title}
                  policyContext={initialData.policy}
                />
              </div>
            ))}
          </div>
        ))
      ) : (
        <div className="text-center text-gray-400 py-4">正在生成...</div>
      )}
    </div>
  );
};

export default OutlineEditor;
