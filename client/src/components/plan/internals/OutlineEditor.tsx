import React, { useState, useEffect } from 'react';
import { OutlineStruct, OutlineSection } from '@/data/contentTypes';
import EditableTitle from './EditableTitle';
import { GenerateOutlineResponse } from '@/data/generateTypes';

interface OutlineEditorProps {
  // We now expect the full initial data object
  initialData: GenerateOutlineResponse;
  onOutlineUpdate?: (outline: OutlineStruct) => void;
}

const OutlineEditor = ({
  initialData,
  onOutlineUpdate,
}: OutlineEditorProps) => {
  // const OutlineEditor = ({ initialData }: OutlineEditorProps) => {
  // The outline data is now managed as state within this component
  const [outline, setOutline] = useState<OutlineStruct>([]);

  // When the initialData from the parent changes, update the state
  useEffect(() => {
    const parsedOutline =
      typeof initialData.outline === 'string'
        ? JSON.parse(initialData.outline)
        : initialData.outline;
    setOutline(parsedOutline);
  }, [initialData.outline]);

  // 在OutlineEditor.tsx中添加回调函数
  const handleOutlineChange = (newOutline: OutlineStruct) => {
    setOutline(newOutline);
    // 添加这行，将更新后的大纲同步到父组件
    onOutlineUpdate?.(newOutline);
  };

  return (
    <div className="space-y-6">
      {outline.map((section, i) => (
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
      ))}
    </div>
  );
};

export default OutlineEditor;
